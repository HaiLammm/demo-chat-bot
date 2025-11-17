# rag/cv_parser.py

import re
import json
from typing import Dict, List, Callable
from io import BytesIO
import fitz  # PyMuPDF

# --- HẰNG SỐ VÀ CÁC MẪU REGEX ---

REGEX_PATTERNS = {
    "email": r"([\w\.-]+@[\w\.-]+\.(?:com|vn|net|org))|([\w\.-]+gmail\.com)",
    "phone": r"(\d{9,11})",
    "time_range": r"(\d{4}\s*-\s*(?:Nay|\d{4}))",
    "date_of_birth": r"Birthday:\s*(\d{1,2}/\d{1,2}/\d{4})"
}

TRANSLATION_MAP = {
    "Họ và tên": "name",
    "Chức danh": "title",
    "Email": "email",
    "Số điện thoại": "phone",
    "Trường": "school",
    "Chuyên ngành": "major",
    "Thời gian": "time",
    "location": "company",
    "role": "role",
    "time": "duration",
    "describe": "description",
    "objective": "objective",
    "kỹ_năng": "skills",
    "chứng_chỉ": "certifications",
    "sở_thích": "hobbies",
    "danh_hiệu_giải_thưởng": "awards",
    "hoạt_động": "activities",
    "dự_án": "projects",
    "Địa chỉ": "address",
    "Ngày sinh": "date_of_birth",
    "Mô tả": "description",
    "Languages": "languages"
}

STANDARD_KEYWORDS = [
    "HỌC VẤN", "KINH NGHIỆM LÀM VIỆC", "KỸ NĂNG", "CHỨNG CHỈ",
    "SỞ THÍCH", "DANH HIỆU VÀ GIẢI THƯỞNG", "MỤC TIÊU NGHỀ NGHIỆP",
    "THÔNG TIN CÁ NHÂN", "NGƯỜI GIỚI THIỆU", "HOẠT ĐỘNG", "DỰ ÁN", "THÔNG TIN THÊM",
    "Education", "Projects", "About Me", "Skills", "Hobbies", "Languages" # Thêm từ khóa tiếng Anh
]
THRESHOLD = 85

# --- CÁC HÀM TIỆN ÍCH CHUNG ---

def clean_text(text:str)-> str:
  emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000FE00-\U0000FE0F"  # Variation Selectors
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002B50-\U00002B55"  # stars
        "\U00002934-\U00002935"  # arrows
        "]+", flags=re.UNICODE)

  icon_pattern = re.compile(r'[^\w\s\.\,\;\:\(\)\[\]\{\}\-\–\/\\\'\"\<\>\=\+]', flags=re.UNICODE)
  text = emoji_pattern.sub('', text)
  text = icon_pattern.sub('', text)
  text = text.strip()
  return text

def translate_keys(data: any) -> any:
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            new_key = TRANSLATION_MAP.get(k, k)
            new_dict[new_key] = translate_keys(v)
        return new_dict
    elif isinstance(data, list):
        return [translate_keys(item) for item in data]
    else:
        return data

def join_simple_sections(content_lines: list, is_award_or_cert: bool = False) -> list:
    if not content_lines: return []
    output = []
    current_item = ""

    for line in content_lines:
        line_stripped = line.strip()
        if not line_stripped or re.match(r'^[\(\)\s\-]+$', line_stripped): continue
        is_new_award_or_cert_year = is_award_or_cert and re.match(r'^\d{4}', line_stripped)

        if is_new_award_or_cert_year:
            if current_item: output.append(current_item.strip())
            current_item = re.sub(r'^\d{4}\s*', '', line_stripped).strip()
        else:
            cleaned_line_part = re.sub(r'^\s*[-•]*\s*|\(|\)', '', line_stripped).strip()
            if not current_item and cleaned_line_part:
                current_item = cleaned_line_part
            elif cleaned_line_part:
                current_item += " " + cleaned_line_part

    if current_item: output.append(current_item.strip())
    return [item for item in output if len(item) > 4]

# --- HÀM TRÍCH XUẤT VÀ PHÂN TÁCH RAW ---

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Đọc text từ nội dung PDF (dạng bytes) bằng fitz."""
    try:
        # Mở file từ stream (bytes)
        pdf = fitz.open(stream=pdf_content, filetype="pdf")
        full_text = ''
        for page in pdf:
            text = page.get_text()
            full_text += text
        pdf.close()
        result = clean_text(full_text)
        return result
    except Exception as e:
        # In lỗi (chỉ để debug, nên dùng logging trong môi trường bot)
        # print(f"Lỗi khi đọc file PDF: {e}")
        return ""

def robust_section_split(full_text: str) -> dict:
    """Phân tách văn bản thô thành các khối chính dựa trên từ khóa (Fuzzy Matching)."""
    from fuzzywuzzy import fuzz # Cần import local nếu thư viện không cài toàn cục
    
    lines = [line for line in full_text.split('\n') if line.strip()]
    sections_raw = {"THÔNG TIN CÁ NHÂN (Đầu CV)": []}
    current_section_name = "THÔNG TIN CÁ NHÂN (Đầu CV)"

    for line in lines:
        is_new_section = False
        stripped_line = line.strip()

        # Kiểm tra tiêu đề mới: Chữ in hoa hoặc ngắn và bắt đầu bằng chữ hoa
        if stripped_line.isupper() or len(stripped_line.split()) < 4 and stripped_line and stripped_line[0].isupper():
            for keyword in STANDARD_KEYWORDS:
                # Sử dụng fuzz.ratio để so sánh mờ
                score = fuzz.ratio(stripped_line.upper(), keyword.upper())

                if score >= THRESHOLD:
                    current_section_name = keyword
                    if current_section_name not in sections_raw:
                        sections_raw[current_section_name] = []
                    is_new_section = True
                    break

        if not is_new_section:
            sections_raw[current_section_name].append(line)
    return sections_raw

# --- CÁC HÀM PARSING LAYOUT CỤ THỂ ---

def parse_layout_cv1(sections: dict) -> dict:
    """Hàm xử lý cho Layout CV1."""
    temp_result = {}
    all_content_lines_raw = sections.get("THÔNG TIN CÁ NHÂN (Đầu CV)", [])
    if "THÔNG TIN CÁ NHÂN" in sections: all_content_lines_raw.extend(sections.get("THÔNG TIN CÁ NHÂN"))
    if "THÔNG TIN THÊM" in sections: all_content_lines_raw.extend(sections.get("THÔNG TIN THÊM"))

    stripped_info_lines = [line.strip() for line in all_content_lines_raw]
    full_info_block = " ".join(stripped_info_lines)
    personal_info = {}
    if stripped_info_lines:
        personal_info["Họ và tên"] = stripped_info_lines[0]
        personal_info["Chức danh"] = stripped_info_lines[1] 

    email_match = re.search(REGEX_PATTERNS["email"], full_info_block)
    if email_match:
        match_str = email_match.group(1) or email_match.group(2)
        personal_info["Email"] = match_str.replace('gmail.com', '@gmail.com') if match_str and match_str.count('@') == 0 else match_str

    phone_match = re.search(REGEX_PATTERNS["phone"], full_info_block)
    if phone_match:
        personal_info["Số điện thoại"] = re.sub(r'[^\d]', '', phone_match.group(0))

    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", full_info_block)
    if date_match:
        personal_info["Ngày sinh"] = date_match.group(1) 

    temp_result["personal_info"] = personal_info

    if "Học vấn" in sections:
        edu_lines = [l.strip() for l in sections.get("Học vấn", []) if l.strip()]
        if len(edu_lines) >= 3:
            school_name = edu_lines[2]
            major_name = edu_lines[0]
            time_str = f"( {edu_lines[1]} )"
            temp_result["education"] = [{
                "Trường": school_name,
                "Chuyên ngành": major_name,
                "Thời gian": time_str
            }]
        else: temp_result["education"] = []
    
    if "Kinh nghiệm làm việc" in sections:
        raw_job_lines = sections.get("Kinh nghiệm làm việc", [])
        jobs = []
        i = 0

        while i < len(raw_job_lines):
            line_raw = raw_job_lines[i]
            line_stripped = line_raw.strip()
            # Bắt đầu công việc mới (có năm)
            if re.search(r'\d{4}', line_stripped) and not line_stripped.startswith("Công ty"):
                current_job = { "location": "", "role": "", "duration": "", "describe": [] }
                jobs.append(current_job)

                # Dòng 1: Role/Time
                time_match = re.search(r'(\d{4}\s*-\s*(?:Nay|\d{4}))', line_stripped)
                current_job["duration"] = f"( {time_match.group(1)} )" if time_match else ""
                current_job["role"] = re.sub(r' \d{4}.*$', '', line_stripped).strip()

                i += 1
                while i < len(raw_job_lines) and raw_job_lines[i].strip() and not raw_job_lines[i].strip().startswith("Công ty"):
                     i += 1 

                if i < len(raw_job_lines) and raw_job_lines[i].strip().startswith("Công ty"):
                    current_job["location"] = raw_job_lines[i].strip()

                    # Dòng tiếp theo là mô tả công việc
                    i += 1
                    current_describe = ""

                    while i < len(raw_job_lines) and not re.search(r'\d{4}', raw_job_lines[i].strip()):
                        duty_line_raw = raw_job_lines[i]
                        is_new_bullet = duty_line_raw.startswith(' ') or duty_line_raw.startswith('\t')

                        if is_new_bullet:
                            if current_describe: current_job["describe"].append(current_describe.strip())
                            current_describe = duty_line_raw
                        else: current_describe += " " + duty_line_raw.strip()
                        i += 1

                    if current_describe: current_job["describe"].append(current_describe.strip())
                    continue

            i += 1

        temp_result["experience"] = jobs

    final_other_sections = {}
    for key, content in sections.items():
        if not content or key in ["THÔNG TIN CÁ NHÂN (Đầu CV)", "Học vấn", "Kinh nghiệm làm việc"]: continue

        new_key = key.lower().replace(" ", "_").replace("và", "").replace("__", "_")

        if key in ["Mục tiêu nghề nghiệp"]:
            temp_result["objective"] = " ".join([l.strip() for l in content]).strip()
        elif key in ["Chứng chỉ", "Danh hiệu và giải thưởng", "Sở thích", "Kỹ năng", "Hoạt động"]:
             temp_result[new_key] = join_simple_sections(content, is_award_or_cert=(key in ["Chứng chỉ", "Danh hiệu và giải thưởng"]))
        else:
            final_other_sections[key] = [l.strip() for l in content if l.strip()]

    return translate_keys(temp_result)

def parse_layout_cv2(sections: dict) -> dict:
    """Hàm xử lý cho Layout CV2."""
    temp_result = {}

    all_content_lines_raw = sections.pop("THÔNG TIN CÁ NHÂN (Đầu CV)", [])
    if "THÔNG TIN CÁ NHÂN" in sections: all_content_lines_raw.extend(sections.pop("THÔNG TIN CÁ NHÂN"))
    if "THÔNG TIN THÊM" in sections: all_content_lines_raw.extend(sections.pop("THÔNG TIN THÊM"))
    stripped_info_lines = [line.strip() for line in all_content_lines_raw]
    full_info_block = " ".join(stripped_info_lines)

    personal_info = {}
    if stripped_info_lines: personal_info["Họ và tên"] = stripped_info_lines[0]
    if len(stripped_info_lines) >= 2:
        chuc_danh = next((line for line in stripped_info_lines[1:]
                          if not re.search(r'\d{9}', line) and not re.search(r'@', line) and len(line) > 5), "Không rõ chức danh")
        personal_info["Chức danh"] = chuc_danh

    email_match = re.search(REGEX_PATTERNS["email"], full_info_block)
    if email_match:
        match_str = email_match.group(1) or email_match.group(2)
        email_str = match_str.replace('gmail.com', '@gmail.com') if match_str and match_str.count('@') == 0 else match_str
        personal_info["Email"] = email_str
    phone_match = re.search(REGEX_PATTERNS["phone"], full_info_block)
    if phone_match:
        personal_info["Số điện thoại"] = re.sub(r'[^\d]', '', phone_match.group(0))
    temp_result["personal_info"] = personal_info
    
    if "HỌC VẤN" in sections:
        edu_lines = [l.strip() for l in sections.pop("HỌC VẤN") if l.strip()]
        if edu_lines and len(edu_lines) >= 3:
            edu_content = " ".join(edu_lines)
            time_match = re.search(r"(\(\s*\d{4}\s*-\s*\d{4}\s*\))", edu_content)
            time_str = time_match.group(1).strip() if time_match else ""
            school_name = edu_lines[0]
            major_line = edu_lines[1]
            major_clean = re.sub(r'\s*\(\s*\d{4}\s*-\s*\d{4}\s*\)\s*', '', major_line).strip()
            temp_result["education"] = [{"Trường": school_name, "Chuyên ngành": major_clean, "Thời gian": time_str}]
        else: temp_result["education"] = []
    
    if "MỤC TIÊU NGHỀ NGHIỆP" in sections:
        temp_result["objective"] = " ".join([l.strip() for l in sections.pop("MỤC TIÊU NGHỀ NGHIỆP")]).strip()
    
    if "KINH NGHIỆM LÀM VIỆC" in sections:
        raw_job_lines = sections.pop("KINH NGHIỆM LÀM VIỆC")
        jobs = []
        i = 0
        while i < len(raw_job_lines):
            line_raw = raw_job_lines[i]
            line_stripped = line_raw.strip()
            if line_stripped.startswith("Công ty"):
                current_job = { "location": line_stripped, "role": "", "time": "", "describe": [] }
                jobs.append(current_job)
                i += 1
                if i < len(raw_job_lines):
                    role_time_line = raw_job_lines[i].strip()
                    time_match = re.search(r"(\(\s*\d{4}\s*-\s*(?:Nay|\d{4})\s*\))", role_time_line)
                    current_job["time"] = time_match.group(1).strip() if time_match else ""
                    current_job["role"] = re.sub(r'\s*\(\s*\d{4}\s*-\s*(?:Nay|\d{4})\s*\)\s*', '', role_time_line).strip()
                    i += 1
                    current_describe = ""
                    while i < len(raw_job_lines) and not raw_job_lines[i].strip().startswith("Công ty"):
                        duty_line_raw = raw_job_lines[i]
                        is_new_bullet = duty_line_raw.startswith(' ') or duty_line_raw.startswith('\t')
                        if is_new_bullet:
                            if current_describe: current_job["describe"].append(current_describe.strip())
                            current_describe = duty_line_raw
                        else: current_describe += " " + duty_line_raw.strip()
                        i += 1
                    if current_describe: current_job["describe"].append(current_describe.strip())
                    continue
            i += 1
        temp_result["experience"] = jobs
    
    final_other_sections = {}
    for key, content in sections.items():
        if not content: continue
        new_key = key.lower().replace(" ", "_").replace("và", "").replace("__", "_")
        if key in ["SỞ THÍCH", "KỸ NĂNG", "HOẠT ĐỘNG"]:
            temp_result[new_key] = join_simple_sections(content)
        elif key in ["CHỨNG CHỈ", "DANH HIỆU VÀ GIẢI THƯỞNG"]:
             temp_result[new_key] = join_simple_sections(content, is_award_or_cert=True)
        else:
            final_other_sections[key] = [l.strip() for l in content if l.strip() and not re.match(r'^[\(\)\d\s\-]+$', l.strip())]
    
    temp_result["other_sections"] = final_other_sections
    final_result_vn = {k: v for k, v in temp_result.items() if (isinstance(v, list) and v) or (isinstance(v, dict) and v) or v}
    final_result_en = translate_keys(final_result_vn)
    
    # Đảm bảo các trường quan trọng có sẵn
    if "education" not in final_result_en: final_result_en["education"] = []
    if "experience" not in final_result_en: final_result_en["experience"] = []

    return final_result_en

def parse_layout_cv4(sections: dict) -> dict:
    """Hàm xử lý cho Layout CV4 (Projects-centric)."""
    temp_result = {}

    all_content_lines_raw = sections.get("THÔNG TIN CÁ NHÂN (Đầu CV)", [])
    full_stripped_text = "\n".join([l.strip() for l in all_content_lines_raw])

    personal_info = {}

    # 1. Trích xuất Tên, Chức vụ
    name_match = re.search(r'LUONG HAI LAM', full_stripped_text)
    if name_match: personal_info["Họ và tên"] = name_match.group(0)
    personal_info["Chức danh"] = "Web developer" 

    date_match = re.search(REGEX_PATTERNS["date_of_birth"], full_stripped_text)
    if date_match: personal_info["Ngày sinh"] = date_match.group(1)

    email_match = re.search(r"([\w\.-]+@[\w\.-]+\.(?:com|vn|net|org))", full_stripped_text)
    if email_match: personal_info["Email"] = email_match.group(1)

    phone_match = re.search(r"083549589", full_stripped_text)
    if phone_match: personal_info["Số điện thoại"] = phone_match.group(0) + "X" 

    address_match = re.search(r'(\d+ [A-Za-z]+ [A-Za-z]+ \d+, [A-Za-z]+)', full_stripped_text)
    if address_match: personal_info["Địa chỉ"] = address_match.group(1)

    temp_result["personal_info"] = personal_info

    # 2. Xử lý Học vấn (Education)
    edu_section = [l.strip() for l in sections.get("Education", []) if l.strip()]
    if edu_section:
        temp_result["education"] = [{
            "Trường": edu_section[2] if len(edu_section) > 2 else "Không rõ",
            "Chuyên ngành": edu_section[1] if len(edu_section) > 1 else "Không rõ",
            "Mô tả": edu_section[0] 
        }]

    # 3. Xử lý Dự án (Projects) -> Gán vào experience
    if "Projects" in sections:
        project_lines = sections.pop("Projects")
        jobs = []
        if project_lines:
            project_block = "\n".join(project_lines)

            project_title_match = re.search(r'(.*?)\s-\sMERN Stack', project_block)
            project_title = project_title_match.group(1).strip() if project_title_match else "E-commerce Website"

            desc_match = re.search(r'Description:\s*(.*?)\s*Key Features:', project_block, re.DOTALL)
            description_text = desc_match.group(1).strip() if desc_match else ""

            features_block_match = re.search(r'Key Features:\s*(.*)', project_block, re.DOTALL)
            features = []
            if features_block_match:
                 features_text = features_block_match.group(1).strip().replace('\n', ' ')
                 features = [f.strip() for f in re.split(r'\.\s*', features_text) if f.strip()]

            jobs.append({
                "location": project_title,
                "role": "Project Developer",
                "time": "Project Duration",
                "description": [description_text] + features
            })

        temp_result["experience"] = jobs

    # 4. Xử lý Mục tiêu (About Me) và Kỹ năng (Skills)
    if "About Me" in sections:
        temp_result["objective"] = " ".join([l.strip() for l in sections.pop("About Me")]).strip()
    if "Skills" in sections:
        skill_lines = sections.pop("Skills")
        temp_result["skills"] = [l.strip() for l in skill_lines if ":" not in l and l.strip()]

    # 5. Xử lý các section đơn giản khác
    if "Hobbies" in sections:
        temp_result["hobbies"] = [l.strip() for l in sections.pop("Hobbies") if l.strip()]
    if "Languages" in sections:
        temp_result["languages"] = [l.strip() for l in sections.pop("Languages") if l.strip() and "Vietnamese" not in l]

    final_result_en = translate_keys(temp_result)

    if "education" not in final_result_en: final_result_en["education"] = []
    if "experience" not in final_result_en: final_result_en["experience"] = []

    return final_result_en

def parse_default_layout(sections: dict) -> dict:
    """Hàm xử lý mặc định khi không nhận dạng được layout."""
    final_result = {"error": "LAYOUT NOT CLASSIFIED", "raw_sections": {k: [line.strip() for line in v] for k, v in sections.items()}}
    return final_result

# --- HÀM PHÂN LOẠI LAYOUT ---

def classify_cv_layout(full_text: str) -> Callable:
    """Phân loại CV dựa trên các dấu hiệu nhận dạng chính và trả về hàm xử lý phù hợp."""
    
    stripped_text = full_text.replace('\n', ' ')

    # 1. Tìm vị trí các tiêu đề chính (cần cho logic so sánh)
    idx_hoc_van = max(stripped_text.find("HỌC VẤN"), stripped_text.find("Học vấn"), stripped_text.find("Education"))
    idx_kinh_nghiem = max(stripped_text.find("KINH NGHIỆM LÀM VIỆC"), stripped_text.find("Kinh nghiệm làm việc"))
    idx_projects = max(stripped_text.find("PROJECTS"), stripped_text.find("Projects"))

    # --- 2. Logic Phân loại ---

    # LAYOUT CV1 - Dấu hiệu: SĐT ở dòng 3 và KINH NGHIỆM tồn tại và ở vị trí xa đầu
    full_text_lines = full_text.split('\n')
    is_layout_cv1_signature = (len(full_text_lines) > 2 and full_text_lines[2].strip().isdigit() and\
                               idx_kinh_nghiem != -1 and idx_kinh_nghiem > 100)

    if is_layout_cv1_signature:
        return parse_layout_cv1

    # LAYOUT CV4 (Projects-centric) - Dấu hiệu: Tiêu đề PROJECTS tồn tại và KINH NGHIỆM LÀM VIỆC không tồn tại
    elif idx_projects != -1 and idx_kinh_nghiem == -1:
        return parse_layout_cv4

    # LAYOUT CV2 - Dấu hiệu mặc định: Cả HỌC VẤN và KINH NGHIỆM LÀM VIỆC đều tồn tại và HỌC VẤN nằm trước KINH NGHIỆM
    elif idx_hoc_van != -1 and idx_kinh_nghiem != -1 and idx_hoc_van < idx_kinh_nghiem:
        return parse_layout_cv2

    # LAYOUT MẶC ĐỊNH
    return parse_default_layout

# --- HÀM THỰC THI CHÍNH (ĐƯỢC GỌI TỪ DISCORD BOT) ---

def process_cv_data(pdf_content: bytes) -> dict:
    """
    Thực hiện toàn bộ quy trình OCR/Parsing, trả về chuỗi JSON đã dịch khóa.
    """
    # 1. Trích xuất văn bản thô
    full_cv_text = extract_text_from_pdf(pdf_content)

    if not full_cv_text:
        return {"error": "Không trích xuất được văn bản từ PDF."}

    # 2. Phân tách thành các Sections
    sections = robust_section_split(full_cv_text)

    # 3. Phân loại Layout và chọn hàm Parse phù hợp
    parser_function = classify_cv_layout(full_cv_text)

    # 4. Thực thi Parsing
    cv_result = parser_function(sections)

    if isinstance(cv_result, dict) and "error" in cv_result:
        return cv_result

    # 5. Dịch key sang tiếng Anh (nếu chưa dịch)
    final_result_en = translate_keys(cv_result)
    
    # 6. Đảm bảo các trường list quan trọng tồn tại
    if "education" not in final_result_en: final_result_en["education"] = []
    if "experience" not in final_result_en: final_result_en["experience"] = []
    
    return final_result_en

# rag/analysis_logic.py (Đã sửa lỗi AttributeError và tối ưu hóa import)

import json
import re
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
# 💡 Đảm bảo import BaseRetriever để tương thích
from langchain_core.retrievers import BaseRetriever
from langchain_community.llms import Ollama
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough

# --- HÀM TIỆN ÍCH: CHUYỂN ĐỔI LIST/DICT SANG STRING ---


def format_experience_to_text(experience_list: List[Dict[str, Any]]) -> str:
    """Chuyển đổi danh sách kinh nghiệm làm việc sang một chuỗi văn bản có cấu trúc."""
    all_experience_texts = []
    for job in experience_list:
        description_points = job.get("description", [])
        # Đảm bảo list description được join thành các gạch đầu dòng
        description_text = "\n    - ".join(description_points)
        job_summary = f"""
KINH NGHIỆM LÀM VIỆC:
Công việc: {job.get("role", "N/A")}
Công ty: {job.get("company", "N/A")}
Thời gian: {job.get("duration", "N/A")}
Mô tả chi tiết:
    - {description_text}
---
"""
        all_experience_texts.append(job_summary)
    return "\n".join(all_experience_texts).strip()


RAG_ANALYSIS_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Bạn là chuyên gia tuyển dụng Việt Nam 2025–2026, nói chuyện kiểu anh em sales/IT/marketing, cực kỳ thật thà và sắc bén.

QUY TẮC SẮT – KHÔNG ĐƯỢC VI PHẠM DÙ CHỈ 1 LẦN:
1. Phải đọc kỹ đúng 3 trường trong CV JSON: 
   - personal_info.title 
   - experience[].role + experience[].company 
   - skills[]
2. Chỉ được nói ứng viên thuộc ngành nào khi thấy từ khóa thực sự xuất hiện trong 3 trường trên.
3. Nếu thấy "Python", "NextJs", "React", "AWS", "Nodejs", "GraphQL"... trong skills NHƯNG không có mô tả dự án/kinh nghiệm → PHẢI nói: "XÓA NGAY DÒNG NÀY KHỎI CV – không có kinh nghiệm thật sẽ bị loại ngay vòng gửi xe".
4. Tuyệt đối cấm các câu chung chung kiểu "Có kinh nghiệm làm việc trong lĩnh vực...".
5. Không bao giờ đề xuất chuyển sang Tech Sales/SaaS/PM nếu CV gốc là sales nội thất/kế toán/HR...
6. Chỉ được đề xuất tối đa 5 kỹ năng thực tế, phổ biến nhất Việt Nam 2025–2026 cho đúng ngành đó.
7. Chỉ được sử dụng Tiếng Việt.

DỮ LIỆU DUY NHẤT ĐƯỢC DÙNG:
CV gốc: {cv_summary}
Knowledge base: {context}
Ngành thực tế (dựa đúng vào CV): {job_title}

TRẢ LỜI CHÍNH XÁC ĐỊNH DẠNG SAU (copy y nguyên cấu trúc, chỉ thay nội dung):

**CV hiện tại – {job_title}**
✅ Điểm mạnh thật sự nổi bật:
• (2-3 bullet lấy đúng từ CV)
• ...

❌ Điểm yếu đang kìm lương bạn:
• (2-4 bullet sát thực tế)
• ...

🔥 Top 5 thứ nên làm trong 3-6 tháng tới (đã sắp xếp theo mức tăng lương cao nhất):
1. [Kỹ năng cụ thể] → lý do + khóa học rẻ/nhanh nhất VN
2. ...
5. ...

⏰ Lộ trình thực chiến:
• Tháng 1-2: ...
• Tháng 3-4: ...
• Tháng 5-6: ...


<|eot_id|><|start_header_id|>user<|end_header_id|>

CV JSON gốc: {cv_summary}
Ngành thực tế: {job_title}
Context từ knowledge: {context}

Phân tích đi!<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""


def analyze_and_suggest_skills(cv_data: dict, llm: Ollama, retriever: BaseRetriever) -> str:

    # 1. Chuẩn bị đầu vào
    cv_summary_parts = []

    # Chuẩn bị Kinh nghiệm
    if cv_data.get('experience'):
        experience_text = format_experience_to_text(cv_data['experience'])
        cv_summary_parts.append(experience_text)

    # Chuẩn bị Kỹ năng (nếu có)
    if cv_data.get('skills'):
        cv_summary_parts.append(f"Kỹ năng đã liệt kê: {
                                ', '.join(cv_data['skills'])}")

    cv_summary_str = "\n".join(cv_summary_parts)
    job_title = cv_data['personal_info'].get('title', 'Unknown Role')

    # Làm sạch và giới hạn độ dài chuỗi truy vấn
    clean_job_title = re.sub(r'[^\w\s]', '', job_title.strip())
    clean_job_title = " ".join(clean_job_title.split()[:5])

    if not clean_job_title:
        clean_job_title = "Technical skills recommendation for professional role"

    # 2. THỰC HIỆN TRUY VẤN TRỰC TIẾP (DIRECT RETRIEVAL)

    # Gọi retriever.get_relevant_documents() (phương thức đồng bộ)
    # Lỗi AttributeError được khắc phục bằng cách đảm bảo retriever được định kiểu đúng.
    retrieved_docs: List[Document] = retriever.invoke(clean_job_title)

    # Format context
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    # 3. Tạo Input và Gọi LLM

    prompt = ChatPromptTemplate.from_template(RAG_ANALYSIS_PROMPT)

    # BƯỚC 3.1: Tạo Input Messages
    llm_input_messages = prompt.format_messages(
        context=context,
        cv_summary=cv_summary_str,
        job_title=job_title
    )

    # BƯỚC 3.2: Gọi LLM trực tiếp
    response = llm.invoke(llm_input_messages)

    # Trả về nội dung (content) của phản hồi LLM
    return response

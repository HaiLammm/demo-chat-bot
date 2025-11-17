# rag/analysis_logic.py (Đã sửa lỗi AttributeError và tối ưu hóa import)

import json
import re 
from typing import List, Dict, Any 

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever # 💡 Đảm bảo import BaseRetriever để tương thích
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


RAG_ANALYSIS_PROMPT = """Bạn là một chuyên gia tuyển dụng và tư vấn nghề nghiệp.
Sử dụng các đoạn ngữ cảnh (context) từ kho kiến thức (knowledge base) và thông tin CV được cung cấp.
Nhiệm vụ của bạn là:
1. **Phân tích** vai trò công việc (`title`) của ứng viên.
2. **Truy xuất** từ ngữ cảnh (context) những KỸ NĂNG/CÔNG CỤ quan trọng (TOP 3-5) nên có cho vai trò đó, nhưng **KHÔNG** được nhắc đến rõ ràng trong CV.
3. **Đưa ra đề xuất cải thiện** chi tiết cho mỗi kỹ năng, giải thích tại sao nó quan trọng.

Context (Kiến thức nền): {context}
---
Thông tin CV đã Parse (Kinh nghiệm và Kỹ năng): {cv_summary}
Vai trò chính của ứng viên: {job_title}
---
Yêu cầu: Hãy tổng hợp và đưa ra đề xuất cải thiện kỹ năng dưới dạng danh sách, ngắn gọn và tập trung.
"""


def analyze_and_suggest_skills(cv_data: dict, llm: Ollama, retriever: BaseRetriever) -> str:
    
    # 1. Chuẩn bị đầu vào
    cv_summary_parts = []
    
    # Chuẩn bị Kinh nghiệm
    if cv_data.get('experience'):
        experience_text = format_experience_to_text(cv_data['experience'])
        cv_summary_parts.append(experience_text)
        
    # Chuẩn bị Kỹ năng (nếu có)
    if cv_data.get('skills'):
        cv_summary_parts.append(f"Kỹ năng đã liệt kê: {', '.join(cv_data['skills'])}")
        
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

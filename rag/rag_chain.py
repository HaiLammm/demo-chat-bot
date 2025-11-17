# rag/rag_chain.py (Phiên bản LCEL)

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
# Import các components LCEL
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from rag.vectorstore import get_vectorstore
import config

def get_rag_chain():
    llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST, client_kwargs={"timeout": 300}, num_thread=4)
    vectorstore = get_vectorstore() 
    # Tăng k lên 4-5 thường cho kết quả tốt hơn k=1
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) 
    
    # Định nghĩa Prompt
    RAG_PROMPT = (
        "Sử dụng thông tin sau để trả lời câu hỏi một cách ngắn gọn. Nếu không biết, nói 'Tôi không biết.'"
        "\n\n"
        "Context: {context}" # Khóa context khớp với đầu vào của chain
        "\n\n"
        "Question: {question}" # Khóa question khớp với đầu vào của chain
    )

    prompt = ChatPromptTemplate.from_template(RAG_PROMPT)

    # Hàm định dạng documents
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Xây dựng Chain LCEL
    rag_chain = (
        # 1. Truy xuất: Lấy chuỗi input (question) và truyền vào retriever
        {"context": RunnablePassthrough() | retriever | format_docs, 
         "question": RunnablePassthrough()}
        # 2. Tạo Prompt: Gửi context và question đã chuẩn bị
        | prompt
        # 3. Gọi LLM
        | llm
        # 4. Trích xuất Output
        | StrOutputParser()
    )
    # Lưu ý: Chain này trả về một CHUỖI, không phải dict {'answer': ...}

    return rag_chain

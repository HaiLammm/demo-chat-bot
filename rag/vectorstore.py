# rag/vectorstore.py (CODE ĐÃ SỬA LỖI VÀ TỐI ƯU)

from langchain_chroma import Chroma
from rag.embeddings import get_embeddings # Giữ import này
import config
import os
import shutil
from .data_loader import load_data 
# 🛑 XÓA DÒNG NÀY: from langchain_ollama import OllamaEmbeddings 
from langchain_core.documents import Document

def get_vectorstore():
    # Hàm này OK, sử dụng get_embeddings() đã cấu hình mxbai-embed-large
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=config.VECTOR_STORE_PATH,
        embedding_function=embeddings
    )
    
def update_vectorstore():
    global vectorstore
    vectorstore_path = config.VECTOR_STORE_PATH
    if os.path.exists(vectorstore_path):
        shutil.rmtree(vectorstore_path, ignore_errors=True)
    
    texts = load_data("data/knowledge.txt")
    if not texts:
        raise ValueError("Không có dữ liệu trong file knowledge.txt")
    
    # Lấy mô hình embedding đã cấu hình (mxbai-embed-large)
    embeddings = get_embeddings() 
    
    # Xử lý nội dung Documents (Chỉ lấy chuỗi nội dung)
    if isinstance(texts[0], Document):
        text_contents = [doc.page_content for doc in texts]
    else:
        text_contents = texts
    
    # Sử dụng hàm from_texts với mô hình EMBEDDING đã cấu hình đúng
    vectorstore = Chroma.from_texts(text_contents, embeddings, persist_directory=vectorstore_path)
    print(f"Vector store đã được cập nhật tại {vectorstore_path}")

# rag/embeddings.py (Đã chỉnh sửa để khắc phục lỗi Ollama API)

from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

# Đảm bảo bạn đã chạy 'ollama pull nomic-embed-text'
OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large:latest" 

def get_embeddings():
    try:
        # Cố gắng sử dụng mô hình Ollama Embedding được chỉ định
        return OllamaEmbeddings(
            model=OLLAMA_EMBEDDING_MODEL, 
            base_url=config.OLLAMA_HOST,
            client_kwargs={"timeout": 300}
        )
    except Exception as e:
        # Fallback nếu Ollama không chạy hoặc model không tìm thấy
        # Log lỗi (tùy chọn)
        return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

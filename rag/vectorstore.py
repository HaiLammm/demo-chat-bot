from langchain_chroma import Chroma
from rag.embeddings import get_embeddings
import config
import os
import shutil
from .data_loader import load_data 
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document

def get_vectorstore():
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
    
    if isinstance(texts[0], Document):
        texts = [doc.page_content for doc in texts]
    
    embeddings = OllamaEmbeddings(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST)
    vectorstore = Chroma.from_texts(texts, embeddings, persist_directory=vectorstore_path)
    print(f"Vector store đã được cập nhật tại {vectorstore_path}")

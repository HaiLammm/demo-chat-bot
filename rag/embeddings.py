from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

def get_embeddings():
    try:
        return OllamaEmbeddings(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST,client_kwargs={"timeout": 300})
    except Exception:
        return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

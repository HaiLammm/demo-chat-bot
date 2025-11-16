import discord
from utils.logger import setup_logger
from rag.data_loader import load_data
from rag.vectorstore import get_vectorstore
from utils.api_helper import test_ollama_connection
import config

logger = setup_logger()

async def on_ready(bot):
    logger.info(f'Bot {bot.user} đã sẵn sàng!')
    print(f'Bot {bot.user} đã sẵn sàng!')
    
    # Kiểm tra Ollama
    if test_ollama_connection():
        print("Ollama kết nối thành công.")
    else:
        print("Lỗi kết nối Ollama!")
    
    # Init RAG
    try:
        get_vectorstore()  # Kiểm tra
        print("Vector store RAG đã sẵn sàng.")
    except Exception:
        docs = load_data()
        get_vectorstore(docs=docs)
        print("Đã tạo vector store RAG mới.")

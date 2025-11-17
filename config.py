import os
from dotenv import load_dotenv
from discord import Intents
import os
from dotenv import load_dotenv
from discord import Intents
# Thêm import Ollama để dễ dàng sử dụng model config
from langchain_community.llms import Ollama 

load_dotenv()

# Discord config
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
INTENTS = Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# Ollama và RAG config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
VECTOR_STORE_PATH = "./rag/vectorstore"
EMBEDDING_MODEL = "all-MiniLM-L6-v2" # Lưu ý: Nên dùng mô hình đa ngôn ngữ cho dữ liệu tiếng Việt

# Other
WELCOME_CHANNEL_ID = int(
    os.getenv("WELCOME_CHANNEL_ID", 0)
)

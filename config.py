import os
from dotenv import load_dotenv
from discord import Intents

load_dotenv()

# Discord config
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
INTENTS = Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# Ollama và RAG config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
VECTOR_STORE_PATH = "./rag/vectorstore"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Other
WELCOME_CHANNEL_ID = int(
    os.getenv("WELCOME_CHANNEL_ID", 0)
)  # ID kênh chào mừng, thay đổi trong .env

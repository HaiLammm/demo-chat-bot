import os
from dotenv import load_dotenv
from discord import Intents
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
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
VECTOR_STORE_PATH = "./rag/vectorstore"
EMBEDDING_MODEL = "all-MiniLM-L6-v2" 
WELCOME_CHANNEL_ID = int(
    os.getenv("WELCOME_CHANNEL_ID", 0)
)

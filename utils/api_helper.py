import requests
import config

def test_ollama_connection():
    """Kiểm tra kết nối Ollama"""
    try:
        response = requests.get(f"{config.OLLAMA_HOST}/api/tags")
        return response.status_code == 200
    except:
        return False

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
import os

def load_data(file_path='data/knowledge.txt'):
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(documents)

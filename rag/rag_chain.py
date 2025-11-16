from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from rag.vectorstore import get_vectorstore
import config

def get_rag_chain():
    llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST,client_kwargs={"timeout": 300}, num_thread=4)
    vectorstore = get_vectorstore() 
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    
    prompt_template = """
    Sử dụng thông tin sau để trả lời câu hỏi một cách ngắn gọn. Nếu không biết, nói "Tôi không biết."
    Context: {context}:
    Question: {question}
    Answer:
    """
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT}
    )

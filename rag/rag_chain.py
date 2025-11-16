from langchain_ollama import ChatOllama
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from rag.vectorstore import get_vectorstore
import config

def get_rag_chain():
    llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_HOST,client_kwargs={"timeout": 300}, num_thread=4)
    vectorstore = get_vectorstore() 
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    
    system_prompt = (
        "Sử dụng thông tin sau để trả lời câu hỏi một cách ngắn gọn. Nếu không biết, nói 'Tôi không biết.'"
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


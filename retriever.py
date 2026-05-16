from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import *

def get_retriever():
    embeddings = OpenAIEmbeddings(
        model="deepseek-embedding",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})
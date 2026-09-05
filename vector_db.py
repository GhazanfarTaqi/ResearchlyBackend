from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEndpointEmbeddings

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    task="feature-extraction",
    huggingfacehub_api_token=os.environ["HF_TOKEN"],
)
vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k":4,
            "fetch_k":10,
            "lambda_mult":0.5
        }
    )

def add_paper_to_vector_store(paper_chunks):
    try:
        vector_store.add_documents(paper_chunks)
    except Exception as e:
        print(f"Error adding paper to vector store: {e}")
from langchain_chroma import Chroma


embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

vector_store.as_retriever(search_kwargs = {"k":4})
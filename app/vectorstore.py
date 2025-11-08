import os

from langchain_chroma import Chroma

from app.config import settings
from app.embeddings import embeddings

os.makedirs(settings.CHROMA_DIR, exist_ok=True)


def get_chroma():
    # This uses the community Chroma wrapper. Replace import if using different package.
    return Chroma(embedding_function=embeddings, persist_directory=settings.CHROMA_DIR)


def get_retriever(k: int = 4):
    store = get_chroma()
    return store.as_retriever(search_kwargs={"k": k})

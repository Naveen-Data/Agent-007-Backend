from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings

embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.EMBEDDING_MODEL, google_api_key=settings.GOOGLE_API_KEY
)

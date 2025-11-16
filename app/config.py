from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google/Gemini API settings - loaded from .env
    GOOGLE_API_KEY: str
    GEMINI_DEFAULT_MODEL: str
    GEMINI_HEAVY_MODEL: str
    EMBEDDING_MODEL: str

    # LangSmith settings - loaded from .env
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "agent_007"

    # Server settings - loaded from .env
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: str = "*"
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    ALLOWED_HEADERS: str = "*"

    # Vectorstore settings - loaded from .env
    CHROMA_DIR: str = "./chroma_db"
    CHROMA_TELEMETRY_ENABLED: bool = False

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields in .env
    )


settings = Settings()

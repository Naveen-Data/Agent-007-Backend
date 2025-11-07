from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str | None = "rag"  # "rag" or "tools" or "heavy"

class ChatResponse(BaseModel):
    reply: str
    used_tools: list[str] | None = []

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models import ChatRequest, ChatResponse
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send(req: ChatRequest):
    if not req.message:
        raise HTTPException(status_code=400, detail="message required")

    try:
        agent = AgentService(mode=req.mode or "rag")
        reply = await agent.answer(req.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(reply=f"Sorry, I encountered an error: {str(e)}")


@router.get("/test")
async def test():
    return {"message": "Chat API is working!"}

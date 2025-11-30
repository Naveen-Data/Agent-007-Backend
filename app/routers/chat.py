import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.di import get_llm, get_tool_registry, get_vectorstore
from app.logging_config import get_logger, log_error, log_performance
from app.models import ChatRequest, ChatResponse, ConversationMessage
from app.services.agent_service import AgentService
from app.services.tool_service import ToolService

router = APIRouter()

logger = get_logger("app.chat")
perf_logger = logging.getLogger("performance")


@router.post("/send", response_model=ChatResponse)
async def send(
    req: ChatRequest,
    request: Request,
    llm=Depends(get_llm),
    vectorstore=Depends(get_vectorstore),
    tool_registry=Depends(get_tool_registry),
):
    if not req.message:
        logger.warning(
            "Empty message received",
            extra={'request_id': getattr(request.state, 'request_id', None)},
        )
        raise HTTPException(status_code=400, detail="message required")

    start_time = time.time()
    request_id = req.request_id or getattr(
        request.state, 'request_id', f'unknown_{int(time.time())}'
    )

    # Log user input with request ID
    logger.info(
        "User input received",
        extra={
            'request_id': request_id,
            'user_input': req.message,
            'mode': req.mode,
            'message_length': len(req.message),
            'history_count': (
                len(req.conversation_history) if req.conversation_history else 0
            ),
            'session_id': req.session_id,
            'event_type': 'user_input',
        },
    )

    try:
        # Build ToolService from registry and construct AgentService with the requested mode
        tool_service = ToolService()
        if tool_registry:
            tool_service.tools = tool_registry

        agent = AgentService(
            mode=(req.mode or "rag"),
            llm=llm,
            tool_service=tool_service,
            vectorstore=vectorstore,
        )

        # Pass conversation history directly to the agent for better memory handling
        reply = await agent.answer_with_history(
            req.message, req.conversation_history or []
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Log LLM response with request ID
        logger.info(
            "LLM response generated",
            extra={
                'request_id': request_id,
                'llm_response': reply,
                'processing_time_ms': processing_time,
                'reply_length': len(reply),
                'mode': req.mode,
                'event_type': 'llm_response',
            },
        )

        # Log successful completion summary
        logger.info(
            "Chat request completed successfully",
            extra={
                'request_id': request_id,
                'processing_time_ms': processing_time,
                'reply_length': len(reply),
                'mode': req.mode,
                'event_type': 'request_completed',
            },
        )

        # Log performance metrics
        log_performance(
            "chat_request",
            processing_time,
            {
                'mode': req.mode,
                'message_length': len(req.message),
                'reply_length': len(reply),
                'history_count': (
                    len(req.conversation_history) if req.conversation_history else 0
                ),
            },
        )

        # Generate session title if requested (for new conversations or empty history)
        session_title = None
        if req.generate_title:
            try:
                summary = await agent.generate_conversation_summary(
                    req.conversation_history or [], req.message
                )
                session_title = summary.title

                logger.info(
                    "Session title generated",
                    extra={
                        'request_id': request_id,
                        'session_title': session_title,
                        'conversation_type': summary.conversation_type,
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to generate session title",
                    extra={'request_id': request_id, 'error': str(e)},
                )

        return ChatResponse(reply=reply, session_title=session_title)

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000

        # Log detailed error information
        error_context = {
            'request_id': request_id,
            'mode': req.mode,
            'message_length': len(req.message),
            'processing_time_ms': processing_time,
            'session_id': req.session_id,
        }

        log_error(logger, e, error_context)

        # Log error response with request ID
        error_reply = "Sorry, I encountered an error while processing your request. Please try again."
        logger.info(
            "Error response sent",
            extra={
                'request_id': request_id,
                'error_response': error_reply,
                'processing_time_ms': processing_time,
                'event_type': 'error_response',
            },
        )

        return ChatResponse(reply=error_reply)


@router.get("/test")
async def test(request: Request):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info("Chat API test endpoint accessed", extra={'request_id': request_id})
    return {"message": "Chat API is working!", "request_id": request_id}

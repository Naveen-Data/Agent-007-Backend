from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import configure_logging


def _maybe_await(value: Any):
    """Await value if it's awaitable, otherwise return it.

    This helper is intentionally small and only used for graceful shutdown of
    adapters that might expose either sync or async close methods.
    """

    if inspect.isawaitable(value):
        return value
    return value


def _build_cors_origins(allowed_origins: Optional[str]) -> List[str]:
    if allowed_origins and allowed_origins != "*":
        return [o.strip() for o in allowed_origins.split(",")]

    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.netlify.app",
        "https://*.vercel.app",
        "https://*.github.io",
        "https://*.amazonaws.com",
        "https://*.awsapprunner.com",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup and shutdown events."""
    logger = configure_logging()
    
    # Startup
    logger.info("Application startup: initializing DI placeholders")
    # Instantiate and attach concrete adapters. Import locally to avoid
    # circular imports at module import time.
    try:
        from app.services.llm_service import LLMService
        from app.vectorstore import get_retriever
        from app.services.tool_service import ToolService

        # Create LLM adapter
        try:
            app.state.llm = LLMService()
            logger.info("LLMService attached to app.state")
        except Exception:
            logger.exception("Failed to initialize LLMService; attaching None")
            app.state.llm = None

        # Create vectorstore retriever for RAG flows
        try:
            retriever = get_retriever()
            app.state.vectorstore = retriever
            logger.info("Vectorstore retriever attached to app.state")
        except Exception:
            logger.exception(
                "Failed to initialize vectorstore retriever; attaching None"
            )
            app.state.vectorstore = None

        # Register tools from ToolService into a registry dict so routers
        # can access tool instances via DI.
        try:
            tool_service = ToolService()
            app.state.tool_registry = tool_service.tools
            logger.info("Tool registry attached to app.state")
        except Exception:
            logger.exception("Failed to initialize ToolService; attaching empty registry")
            app.state.tool_registry = {}
    except Exception:
        logger.exception("Unexpected error during DI startup; leaving adapters as None/empty")
        app.state.llm = None
        app.state.vectorstore = None
        app.state.tool_registry = {}

    yield  # Application runs here

    # Shutdown
    logger.info("Application shutdown: closing adapters if present")
    # Close LLM client if it has a close method
    llm = getattr(app.state, "llm", None)
    if llm is not None and hasattr(llm, "close"):
        try:
            res = llm.close()
            maybe = _maybe_await(res)
            if inspect.isawaitable(maybe):
                await maybe
        except Exception:
            logger.exception("Error while closing LLM client")

    # Close vectorstore if it exposes a close or shutdown method
    vs = getattr(app.state, "vectorstore", None)
    if vs is not None:
        close_fn = getattr(vs, "close", None) or getattr(vs, "shutdown", None)
        if close_fn is not None:
            try:
                res = close_fn()
                maybe = _maybe_await(res)
                if inspect.isawaitable(maybe):
                    await maybe
            except Exception:
                logger.exception("Error while closing VectorStore client")


def create_app(custom_settings: Optional[Any] = None) -> FastAPI:
    """Create and wire the FastAPI application.

    This factory centralizes DI wiring and attaches placeholders for the
    concrete adapters to `app.state` so routers and services can access them
    via dependency providers. Concrete implementations should be created in
    lifespan handlers or injected by higher-level orchestration.
    """

    app = FastAPI(title="agent_007", lifespan=lifespan)

    app.state.settings = custom_settings or settings

    origins = _build_cors_origins(app.state.settings.ALLOWED_ORIGINS)

    # Configure CORS from environment settings
    allowed_methods = getattr(app.state.settings, 'ALLOWED_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
    allowed_headers = getattr(app.state.settings, 'ALLOWED_HEADERS', '*').split(',')
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=False,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        allow_origin_regex=r"https://.*(netlify\.app|vercel\.app|github\.io|amazonaws\.com|awsapprunner\.com)$",
    )

    # include routers (imported locally to avoid circular imports with DI providers)
    from app.routers import chat, mcp_server, logs, tools_config

    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(mcp_server.router, prefix="/api/mcp", tags=["mcp", "tools"])
    app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
    app.include_router(tools_config.router, prefix="/api/tools", tags=["tools", "configuration"])

    return app


def get_settings(request: Request) -> Any:
    return request.app.state.settings


def get_llm(request: Request) -> Any:
    return request.app.state.llm


def get_vectorstore(request: Request) -> Any:
    return request.app.state.vectorstore


def get_tool_registry(request: Request) -> Dict[str, Any]:
    return request.app.state.tool_registry


def get_agent_service(request: Request) -> Any:
    """Provider for `AgentService` constructed with available app-state adapters.

    Falls back to the default concrete implementations when adapters are not
    attached to `app.state`, keeping backward compatibility.
    """
    from app.services.agent_service import AgentService
    from app.services.tool_service import ToolService

    llm = getattr(request.app.state, "llm", None)
    vectorstore = getattr(request.app.state, "vectorstore", None)

    # Build ToolService, optionally replacing the tools mapping with a
    # pre-registered registry (useful for tests or external wiring).
    tool_service = ToolService()
    registry = getattr(request.app.state, "tool_registry", None)
    if registry:
        try:
            tool_service.tools = registry
        except Exception:
            # If the registry is not compatible, fall back silently and let
            # existing ToolService continue managing tools.
            pass

    from app.constants import AgentConstants
    return AgentService(mode=AgentConstants.MODE_CHAT, llm=llm, tool_service=tool_service, vectorstore=vectorstore)

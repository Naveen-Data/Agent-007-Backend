from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

"""
Support running the app in several ways:
1. As a package from project root: `uvicorn app.main:app` (preferred).
2. As a top-level module inside the `app/` directory: `uvicorn main:app`.
3. As an imported module in other execution contexts.

Try imports in this order: package absolute imports, top-level module imports
(when working directory is `app/`), and fall back to relative imports as a last
resort.
"""


    # Preferred when running from the project root: `uvicorn app.main:app`
from app.config import settings
from app.logging_config import configure_logging
from app.routers import chat, mcp_server
# Fallback for running as a top-level module inside `app/` directory

logger = configure_logging()

app = FastAPI(title="agent_007")

# Configure CORS origins for production deployment
if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*":
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
else:
    # Default origins for development and common deployment platforms
    origins = [
        "http://localhost:3000",  # Local development
        "http://localhost:3001",  # Alternative local port
        "https://*.netlify.app",  # Netlify deployments
        "https://*.vercel.app",   # Vercel deployments
        "https://*.github.io",    # GitHub Pages
        "https://*.amazonaws.com", # AWS S3/CloudFront
        "https://*.awsapprunner.com", # AWS App Runner
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=False,  # Set to False for production security
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*(netlify\.app|vercel\.app|github\.io|amazonaws\.com|awsapprunner\.com)$"
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(mcp_server.router, prefix="/api/mcp", tags=["mcp", "tools"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "message": "Agent 007 Backend API",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat/send",
            "mcp": "/api/mcp",
            "tools": "/api/mcp/tools",
            "docs": "/docs"
        }
    }

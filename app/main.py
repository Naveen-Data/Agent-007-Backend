from dotenv import load_dotenv

from app.core.di import create_app
from app.logging_config import get_logger, setup_application_logging
from app.middleware import setup_logging_middleware

# Load environment variables from .env file
load_dotenv()

# Setup comprehensive logging before app creation
logging_config = setup_application_logging()
logger = get_logger("main")

# Create app via DI factory. Concrete adapters are attached to `app.state`
# during startup/shutdown lifecycle handlers or by a bootstrapper.
app = create_app()

# Setup logging middleware
setup_logging_middleware(app)

# Log application startup
logger.info("Agent 007 Backend starting up", extra={'version': '1.0.0'})


@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "ok", "timestamp": "2025-11-16"}


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Agent 007 Backend API",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat/send",
            "mcp": "/api/mcp",
            "tools": "/api/mcp/tools",
            "docs": "/docs",
        },
    }

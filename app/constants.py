# Application Constants
# Centralized constants for Agent 007 - Environment variables are kept in config.py

from typing import Dict, Final, List

# =============================================================================
# API CONSTANTS
# =============================================================================


class APIConstants:
    """API-related constants"""

    # Response Messages
    SUCCESS_MESSAGE: Final[str] = "Operation completed successfully"
    ERROR_MESSAGE: Final[str] = "An error occurred"
    INVALID_REQUEST_MESSAGE: Final[str] = "Invalid request format"
    UNAUTHORIZED_MESSAGE: Final[str] = "Unauthorized access"

    # HTTP Status Codes (for reference)
    HTTP_OK: Final[int] = 200
    HTTP_CREATED: Final[int] = 201
    HTTP_BAD_REQUEST: Final[int] = 400
    HTTP_UNAUTHORIZED: Final[int] = 401
    HTTP_NOT_FOUND: Final[int] = 404
    HTTP_INTERNAL_ERROR: Final[int] = 500

    # Request/Response Limits
    MAX_REQUEST_SIZE: Final[int] = 10_000_000  # 10MB
    MAX_RESPONSE_SIZE: Final[int] = 50_000_000  # 50MB
    MAX_RETRIES: Final[int] = 3
    DEFAULT_TIMEOUT: Final[int] = 30  # seconds
    RATE_LIMIT_REQUESTS: Final[int] = 100
    RATE_LIMIT_WINDOW: Final[int] = 3600  # 1 hour


# =============================================================================
# LOGGING CONSTANTS
# =============================================================================


class LoggingConstants:
    """Logging-related constants"""

    # Log Levels
    LOG_LEVEL_DEBUG: Final[str] = "DEBUG"
    LOG_LEVEL_INFO: Final[str] = "INFO"
    LOG_LEVEL_WARNING: Final[str] = "WARNING"
    LOG_LEVEL_ERROR: Final[str] = "ERROR"
    LOG_LEVEL_CRITICAL: Final[str] = "CRITICAL"

    # Log Formats
    DEFAULT_LOG_FORMAT: Final[str] = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    DETAILED_LOG_FORMAT: Final[str] = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s:%(lineno)-4d | %(message)s"
    )

    # Log File Settings
    MAX_LOG_FILE_SIZE: Final[int] = 10_000_000  # 10MB
    MAX_LOG_FILES: Final[int] = 5
    LOG_ROTATION_WHEN: Final[str] = "midnight"
    LOG_BACKUP_COUNT: Final[int] = 7

    # Request ID Settings
    REQUEST_ID_LENGTH: Final[int] = 12
    REQUEST_ID_PREFIX: Final[str] = "req_"


# =============================================================================
# AGENT CONSTANTS
# =============================================================================


class AgentConstants:
    """Agent behavior constants"""

    # Response Modes
    MODE_RAG: Final[str] = "rag"
    MODE_TOOLS: Final[str] = "tools"
    MODE_CHAT: Final[str] = "chat"  # Default conversational mode
    MODE_EXPRESSIVE: Final[str] = "expressive"  # Heavy model for complex responses
    MODE_ENHANCED_TOOLS: Final[str] = "enhanced_tools"

    # Default Prompts
    DEFAULT_SYSTEM_PROMPT: Final[
        str
    ] = """<system>
You are Agent 007, a helpful AI assistant.
</system>"""
    RAG_SYSTEM_PROMPT: Final[
        str
    ] = """<system>
You are an AI assistant with access to relevant documents and conversation history.
Use the provided context to answer questions accurately. If the context doesn't contain enough information, 
acknowledge this and provide the best answer you can with available information.
</system>"""

    TOOL_SYSTEM_PROMPT: Final[
        str
    ] = """<system>
You are Agent 007, an AI assistant with access to various tools.
Analyze the user's request and determine which tools would be most helpful to provide an accurate response.
Use tools when they can provide more current, specific, or detailed information than your training data.
</system>"""

    ENHANCED_TOOL_SYSTEM_PROMPT: Final[
        str
    ] = """<system>
You are Agent 007, an advanced AI agent with sophisticated tool usage capabilities. 
You have access to multiple tools and can chain them together for complex tasks. 
Analyze the user's question deeply and determine the optimal tool strategy with detailed reasoning.
</system>"""

    # Performance Settings
    MAX_CONVERSATION_HISTORY: Final[int] = 20
    MAX_CONTEXT_LENGTH: Final[int] = 8000
    MAX_TOOL_EXECUTIONS: Final[int] = 5
    TOOL_EXECUTION_TIMEOUT: Final[int] = 30  # seconds

    # Conversation Settings
    CONVERSATION_SUMMARY_THRESHOLD: Final[int] = 10  # messages before auto-summary
    AUTO_TITLE_GENERATION: Final[bool] = True
    MAX_TITLE_LENGTH: Final[int] = 60


# =============================================================================
# TOOL CONSTANTS
# =============================================================================


class ToolConstants:
    """Tool-related constants"""

    # Tool Categories
    CATEGORY_INFORMATION: Final[str] = "Information"
    CATEGORY_DEVELOPMENT: Final[str] = "Development"
    CATEGORY_KNOWLEDGE_BASE: Final[str] = "Knowledge Base"
    CATEGORY_UTILITY: Final[str] = "Utility"
    CATEGORY_OTHER: Final[str] = "Other"

    # Tool Status
    STATUS_ENABLED: Final[str] = "enabled"
    STATUS_DISABLED: Final[str] = "disabled"
    STATUS_ERROR: Final[str] = "error"

    # Tool Execution
    DEFAULT_TOOL_TIMEOUT: Final[int] = 15  # seconds
    MAX_TOOL_OUTPUT_LENGTH: Final[int] = 10000
    TOOL_RETRY_ATTEMPTS: Final[int] = 2

    # Tool Names (for consistency)
    TOOL_WEB_SEARCH: Final[str] = "web_search"
    TOOL_WEATHER: Final[str] = "weather"
    TOOL_GITHUB_ISSUES: Final[str] = "github_issues"
    TOOL_HTTP: Final[str] = "http_tool"
    TOOL_VECTOR_QUERY: Final[str] = "vector_query"


# =============================================================================
# DATABASE CONSTANTS
# =============================================================================


class DatabaseConstants:
    """Database-related constants"""

    # Vector Store Settings
    DEFAULT_SIMILARITY_THRESHOLD: Final[float] = 0.7
    MAX_SEARCH_RESULTS: Final[int] = 10
    DEFAULT_SEARCH_RESULTS: Final[int] = 4
    EMBEDDING_DIMENSIONS: Final[int] = 768

    # ChromaDB Settings
    CHROMA_COLLECTION_NAME: Final[str] = "agent_007_knowledge"
    CHROMA_DISTANCE_FUNCTION: Final[str] = "cosine"
    CHROMA_BATCH_SIZE: Final[int] = 100


# UI Constants are now in frontend repository only

# =============================================================================
# SECURITY CONSTANTS
# =============================================================================


class SecurityConstants:
    """Security-related constants"""

    # Input Validation
    MAX_INPUT_LENGTH: Final[int] = 10000
    ALLOWED_FILE_EXTENSIONS: Final[List[str]] = ['.txt', '.md', '.json', '.csv']
    MAX_FILE_SIZE: Final[int] = 5_000_000  # 5MB

    # Rate Limiting
    DEFAULT_RATE_LIMIT: Final[int] = 60  # requests per minute
    BURST_RATE_LIMIT: Final[int] = 10  # requests per second

    # CORS Settings are now environment-based (see config.py)


# =============================================================================
# ERROR CONSTANTS
# =============================================================================


class ErrorConstants:
    """Error messages and codes"""

    # Tool Errors
    TOOL_NOT_FOUND: Final[str] = "Tool not found"
    TOOL_EXECUTION_FAILED: Final[str] = "Tool execution failed"
    TOOL_TIMEOUT: Final[str] = "Tool execution timed out"
    TOOL_DISABLED: Final[str] = "Tool is currently disabled"

    # Agent Errors
    AGENT_INITIALIZATION_ERROR: Final[str] = "Failed to initialize agent"
    CONVERSATION_PROCESSING_ERROR: Final[str] = "Error processing conversation"
    INVALID_MODE_ERROR: Final[str] = "Invalid agent mode specified"

    # API Errors
    INVALID_JSON_ERROR: Final[str] = "Invalid JSON format"
    MISSING_FIELD_ERROR: Final[str] = "Required field missing"
    VALIDATION_ERROR: Final[str] = "Input validation failed"

    # System Errors
    DATABASE_CONNECTION_ERROR: Final[str] = "Database connection failed"
    EXTERNAL_SERVICE_ERROR: Final[str] = "External service unavailable"
    CONFIGURATION_ERROR: Final[str] = "Configuration error"


# =============================================================================
# PERFORMANCE CONSTANTS
# =============================================================================


class PerformanceConstants:
    """Performance monitoring constants"""

    # Timing Thresholds (in seconds)
    SLOW_REQUEST_THRESHOLD: Final[float] = 5.0
    VERY_SLOW_REQUEST_THRESHOLD: Final[float] = 10.0
    TIMEOUT_WARNING_THRESHOLD: Final[float] = 20.0

    # Memory Thresholds (in MB)
    HIGH_MEMORY_THRESHOLD: Final[int] = 512
    CRITICAL_MEMORY_THRESHOLD: Final[int] = 1024

    # Monitoring Intervals
    HEALTH_CHECK_INTERVAL: Final[int] = 60  # seconds
    METRICS_COLLECTION_INTERVAL: Final[int] = 300  # 5 minutes
    LOG_ROTATION_INTERVAL: Final[int] = 86400  # 24 hours


# =============================================================================
# FEATURE FLAGS
# =============================================================================


class FeatureFlags:
    """Feature toggle constants"""

    # Core Features
    ENABLE_RAG: Final[bool] = True
    ENABLE_TOOLS: Final[bool] = True
    ENABLE_CONVERSATION_SUMMARY: Final[bool] = True
    ENABLE_AUTO_NAMING: Final[bool] = True

    # Advanced Features
    ENABLE_PERFORMANCE_MONITORING: Final[bool] = True
    ENABLE_DETAILED_LOGGING: Final[bool] = True
    ENABLE_METRICS_COLLECTION: Final[bool] = True
    ENABLE_DEBUG_MODE: Final[bool] = False

    # UI Features
    ENABLE_DARK_MODE: Final[bool] = True
    ENABLE_TOOL_CONFIGURATION_UI: Final[bool] = True
    ENABLE_CHAT_EXPORT: Final[bool] = True
    ENABLE_SESSION_PERSISTENCE: Final[bool] = True


# =============================================================================
# VERSION CONSTANTS
# =============================================================================


class VersionConstants:
    """Version information"""

    APP_VERSION: Final[str] = "1.0.0"
    API_VERSION: Final[str] = "v1"
    CONFIG_VERSION: Final[str] = "1.0"
    MINIMUM_PYTHON_VERSION: Final[str] = "3.11"

    # Component Versions
    FRONTEND_COMPATIBLE_VERSION: Final[str] = "1.0.x"
    BACKEND_COMPATIBLE_VERSION: Final[str] = "1.0.x"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_all_constants() -> Dict[str, Dict[str, any]]:
    """Get all constants organized by category"""
    return {
        "api": {
            k: v for k, v in APIConstants.__dict__.items() if not k.startswith('_')
        },
        "logging": {
            k: v for k, v in LoggingConstants.__dict__.items() if not k.startswith('_')
        },
        "agent": {
            k: v for k, v in AgentConstants.__dict__.items() if not k.startswith('_')
        },
        "tools": {
            k: v for k, v in ToolConstants.__dict__.items() if not k.startswith('_')
        },
        "database": {
            k: v for k, v in DatabaseConstants.__dict__.items() if not k.startswith('_')
        },
        "security": {
            k: v for k, v in SecurityConstants.__dict__.items() if not k.startswith('_')
        },
        "errors": {
            k: v for k, v in ErrorConstants.__dict__.items() if not k.startswith('_')
        },
        "performance": {
            k: v
            for k, v in PerformanceConstants.__dict__.items()
            if not k.startswith('_')
        },
        "features": {
            k: v for k, v in FeatureFlags.__dict__.items() if not k.startswith('_')
        },
        "version": {
            k: v for k, v in VersionConstants.__dict__.items() if not k.startswith('_')
        },
    }


def get_constants_by_category(category: str) -> Dict[str, any]:
    """Get constants for a specific category"""
    all_constants = get_all_constants()
    return all_constants.get(category, {})

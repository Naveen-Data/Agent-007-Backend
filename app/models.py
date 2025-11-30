from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.constants import AgentConstants


class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str | None = (
        AgentConstants.MODE_CHAT
    )  # "chat" (default), "rag", "tools", "expressive", or "enhanced_tools"
    conversation_history: list[ConversationMessage] | None = []
    request_id: str | None = None
    generate_title: bool = False  # Whether to generate a title for this conversation


class ChatResponse(BaseModel):
    reply: str
    used_tools: list[str] | None = []
    session_title: str | None = None  # Generated title for new conversations


# Enhanced Pydantic models for structured LLM responses
class ToolSelection(BaseModel):
    """Structured model for tool selection responses"""

    selected_tool: str = Field(..., description="The selected tool name or 'llm_only'")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the selected tool"
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why this tool was selected"
    )
    confidence: float = Field(default=1.0, description="Confidence level (0.0 to 1.0)")

    model_config = ConfigDict(extra="ignore")


class RAGResponse(BaseModel):
    """Structured model for RAG responses"""

    answer: str = Field(..., description="The main response to the user")
    sources_used: List[str] = Field(
        default_factory=list, description="List of document sources referenced"
    )
    context_relevance: float = Field(
        default=1.0, description="How relevant the retrieved context was (0.0 to 1.0)"
    )

    model_config = ConfigDict(extra="ignore")


class ToolExecutionResult(BaseModel):
    """Structured model for tool execution results"""

    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: str = Field(..., description="The result or output from the tool")
    parameters_used: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters that were passed to the tool"
    )
    execution_time: Optional[float] = Field(
        None, description="Time taken to execute the tool in seconds"
    )

    model_config = ConfigDict(extra="ignore")


class GeneralResponse(BaseModel):
    """Structured model for general LLM responses"""

    response: str = Field(..., description="The main response content")
    response_type: Literal["informational", "question", "instruction", "error"] = Field(
        default="informational", description="Type of response"
    )
    topics: List[str] = Field(
        default_factory=list, description="Main topics covered in the response"
    )

    model_config = ConfigDict(extra="ignore")


class ConversationAnalysis(BaseModel):
    """Model for analyzing conversation context"""

    main_topic: str = Field(..., description="Primary topic of the conversation")
    user_intent: str = Field(..., description="Inferred user intent")
    context_summary: str = Field(
        ..., description="Brief summary of conversation context"
    )
    relevant_history: List[str] = Field(
        default_factory=list, description="Key points from conversation history"
    )

    model_config = ConfigDict(extra="ignore")


class ConversationSummary(BaseModel):
    """Model for generating conversation summaries and titles"""

    title: str = Field(
        ..., description="Concise title for the conversation (3-5 words)"
    )
    summary: str = Field(..., description="Brief summary of the conversation")
    key_topics: List[str] = Field(
        default_factory=list, description="Main topics discussed"
    )
    conversation_type: Literal[
        "question_answer",
        "problem_solving",
        "information_request",
        "casual_chat",
        "technical_discussion",
    ] = Field(default="question_answer", description="Type of conversation")

    model_config = ConfigDict(extra="ignore")

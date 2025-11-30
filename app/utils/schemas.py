"""Define Pydantic schemas for API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.constants import AgentConstants


class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolExecutionResponse(BaseModel):
    result: str
    tool_name: str
    success: bool
    error: Optional[str] = None


class AgentRequest(BaseModel):
    message: str
    mode: str = AgentConstants.MODE_CHAT
    tools_enabled: bool = True


class AgentResponse(BaseModel):
    reply: str
    mode: str
    tools_used: List[str] = []
    success: bool = True


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, str] = {}


class ToolListResponse(BaseModel):
    tools: List[ToolInfo]
    count: int

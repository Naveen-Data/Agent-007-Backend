from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.tool_service import ToolService

router = APIRouter()
tool_service = ToolService()


class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    result: str
    tool_name: str
    success: bool


@router.get("/mcp")
def mcp_entrypoint():
    return {
        "message": "MCP server is running!",
        "tools": tool_service.get_available_tools(),
    }


@router.get("/mcp/tools")
def list_tools():
    """List all available tools"""
    return {"tools": tool_service.get_available_tools()}


@router.post("/mcp/execute", response_model=ToolResponse)
def execute_tool(request: ToolRequest):
    """Execute a specific tool with parameters"""
    try:
        result = tool_service.execute_tool(request.tool_name, **request.parameters)
        return ToolResponse(result=result, tool_name=request.tool_name, success=True)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error executing tool '{request.tool_name}': {str(e)}",
        )

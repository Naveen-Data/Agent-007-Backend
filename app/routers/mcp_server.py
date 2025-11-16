from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.di import get_tool_registry

router = APIRouter()


class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    result: str
    tool_name: str
    success: bool


@router.get("/mcp")
def mcp_entrypoint(tool_registry: Dict[str, Any] = Depends(get_tool_registry)):
    return {
        "message": "MCP server is running!",
        "tools": {k: getattr(v, 'description', '') for k, v in tool_registry.items()},
    }


@router.get("/mcp/tools")
def list_tools(tool_registry: Dict[str, Any] = Depends(get_tool_registry)):
    """List all available tools"""
    return {
        "tools": {k: getattr(v, 'description', '') for k, v in tool_registry.items()}
    }


@router.post("/mcp/execute", response_model=ToolResponse)
def execute_tool(
    request: ToolRequest, tool_registry: Dict[str, Any] = Depends(get_tool_registry)
):
    """Execute a specific tool with parameters"""
    try:
        if request.tool_name not in tool_registry:
            available = ", ".join(tool_registry.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Unknown tool '{request.tool_name}'. Available: {available}",
            )

        tool = tool_registry[request.tool_name]
        if not hasattr(tool, "run"):
            raise HTTPException(status_code=500, detail="Tool does not implement run()")
        result = tool.run(**request.parameters)

        # If standardized ToolResult
        if hasattr(result, "success") and hasattr(result, "output"):
            return ToolResponse(
                result=result.output or (result.error or ""),
                tool_name=request.tool_name,
                success=bool(result.success),
            )

        # Fallback raw result
        return ToolResponse(
            result=str(result), tool_name=request.tool_name, success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error executing tool '{request.tool_name}': {str(e)}",
        )

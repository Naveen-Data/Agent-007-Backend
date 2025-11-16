from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List
import logging

from app.tools_config import (
    get_tool_availability,
    get_enabled_tools,
    is_tool_enabled,
    ToolConfig,
    TOOL_DESCRIPTIONS,
    TOOL_CATEGORIES,
)
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger("app.tools_config")


@router.get("/available")
async def get_available_tools(request: Request):
    """Get list of all available tools with their status"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    logger.info("Tools availability requested", extra={'request_id': request_id})

    availability = get_tool_availability()
    tools_info = {}

    for tool_name in TOOL_DESCRIPTIONS:
        tools_info[tool_name] = {
            "name": tool_name,
            "enabled": availability.get(tool_name, False),
            "description": TOOL_DESCRIPTIONS[tool_name],
            "category": TOOL_CATEGORIES.get(tool_name, "Other"),
        }

    return {
        "tools": tools_info,
        "enabled_count": len(get_enabled_tools()),
        "total_count": len(TOOL_DESCRIPTIONS),
    }


@router.get("/enabled")
async def get_enabled_tools_list(request: Request):
    """Get list of currently enabled tools"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    enabled_tools = get_enabled_tools()

    logger.info(
        "Enabled tools requested",
        extra={
            'request_id': request_id,
            'enabled_tools': enabled_tools,
            'count': len(enabled_tools),
        },
    )

    return {"enabled_tools": enabled_tools, "count": len(enabled_tools)}


@router.post("/configure")
async def configure_tools(request: Request, tool_config: Dict[str, bool]):
    """Configure which tools are enabled/disabled"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    # Validate tool names
    invalid_tools = [tool for tool in tool_config if tool not in TOOL_DESCRIPTIONS]
    if invalid_tools:
        logger.warning(
            "Invalid tools in configuration request",
            extra={'request_id': request_id, 'invalid_tools': invalid_tools},
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tool names: {invalid_tools}. Available tools: {list(TOOL_DESCRIPTIONS.keys())}",
        )

    # Apply configuration
    changes = []
    for tool_name, enabled in tool_config.items():
        current_status = is_tool_enabled(tool_name)
        if current_status != enabled:
            ToolConfig.set_tool_enabled(tool_name, enabled)
            changes.append(
                {"tool": tool_name, "old_status": current_status, "new_status": enabled}
            )

    logger.info(
        "Tool configuration updated",
        extra={
            'request_id': request_id,
            'changes': changes,
            'total_changes': len(changes),
        },
    )

    return {
        "message": f"Updated configuration for {len(changes)} tools",
        "changes": changes,
        "current_status": get_tool_availability(),
    }


@router.post("/enable/{tool_name}")
async def enable_tool(tool_name: str, request: Request):
    """Enable a specific tool"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    if tool_name not in TOOL_DESCRIPTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(TOOL_DESCRIPTIONS.keys())}",
        )

    was_enabled = is_tool_enabled(tool_name)
    ToolConfig.set_tool_enabled(tool_name, True)

    logger.info(
        "Tool enabled",
        extra={
            'request_id': request_id,
            'tool_name': tool_name,
            'was_enabled': was_enabled,
        },
    )

    return {
        "message": f"Tool '{tool_name}' enabled",
        "tool_name": tool_name,
        "enabled": True,
        "was_enabled": was_enabled,
    }


@router.post("/disable/{tool_name}")
async def disable_tool(tool_name: str, request: Request):
    """Disable a specific tool"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    if tool_name not in TOOL_DESCRIPTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(TOOL_DESCRIPTIONS.keys())}",
        )

    was_enabled = is_tool_enabled(tool_name)
    ToolConfig.set_tool_enabled(tool_name, False)

    logger.info(
        "Tool disabled",
        extra={
            'request_id': request_id,
            'tool_name': tool_name,
            'was_enabled': was_enabled,
        },
    )

    return {
        "message": f"Tool '{tool_name}' disabled",
        "tool_name": tool_name,
        "enabled": False,
        "was_enabled": was_enabled,
    }


@router.post("/reset")
async def reset_tools_config(request: Request):
    """Reset all tools to default enabled state"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    ToolConfig.enable_all_tools()

    logger.info(
        "Tools configuration reset to defaults",
        extra={'request_id': request_id, 'enabled_tools': get_enabled_tools()},
    )

    return {
        "message": "All tools reset to enabled state",
        "enabled_tools": get_enabled_tools(),
        "count": len(get_enabled_tools()),
    }


@router.get("/categories")
async def get_tool_categories(request: Request):
    """Get tools grouped by categories"""
    request_id = getattr(request.state, 'request_id', 'unknown')

    categories = {}
    availability = get_tool_availability()

    for tool_name, description in TOOL_DESCRIPTIONS.items():
        category = TOOL_CATEGORIES.get(tool_name, "Other")
        if category not in categories:
            categories[category] = []

        categories[category].append(
            {
                "name": tool_name,
                "description": description,
                "enabled": availability.get(tool_name, False),
            }
        )

    logger.info(
        "Tool categories requested",
        extra={'request_id': request_id, 'category_count': len(categories)},
    )

    return {"categories": categories, "total_categories": len(categories)}

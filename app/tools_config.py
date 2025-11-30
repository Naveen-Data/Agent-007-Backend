# Tool Configuration Constants
# Centralized tool management for easy enable/disable

import os
from typing import Dict, List

from app.constants import ToolConstants

# Tool availability flags - set to False to disable specific tools
TOOL_AVAILABILITY = {
    ToolConstants.TOOL_WEB_SEARCH: True,
    ToolConstants.TOOL_WEATHER: True,
    ToolConstants.TOOL_GITHUB_ISSUES: True,
    ToolConstants.TOOL_HTTP: True,
    ToolConstants.TOOL_VECTOR_QUERY: True,
}

# Tool descriptions for UI display
TOOL_DESCRIPTIONS = {
    ToolConstants.TOOL_WEB_SEARCH: "Search the web for current information",
    ToolConstants.TOOL_WEATHER: "Get weather information for any location",
    ToolConstants.TOOL_GITHUB_ISSUES: "Search and manage GitHub repository issues",
    ToolConstants.TOOL_HTTP: "Make HTTP requests to APIs and web services",
    ToolConstants.TOOL_VECTOR_QUERY: "Query the knowledge base for relevant information",
}

# Tool categories for grouping
TOOL_CATEGORIES = {
    ToolConstants.TOOL_WEB_SEARCH: ToolConstants.CATEGORY_INFORMATION,
    ToolConstants.TOOL_WEATHER: ToolConstants.CATEGORY_INFORMATION,
    ToolConstants.TOOL_GITHUB_ISSUES: ToolConstants.CATEGORY_DEVELOPMENT,
    ToolConstants.TOOL_HTTP: ToolConstants.CATEGORY_DEVELOPMENT,
    ToolConstants.TOOL_VECTOR_QUERY: ToolConstants.CATEGORY_KNOWLEDGE_BASE,
}


# Environment-based overrides (useful for different deployments)
def get_tool_availability() -> Dict[str, bool]:
    """Get current tool availability based on config and environment variables"""
    availability = TOOL_AVAILABILITY.copy()

    # Allow environment variables to override defaults
    for tool_name in availability:
        env_var = f"ENABLE_TOOL_{tool_name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            availability[tool_name] = env_value.lower() in ('true', '1', 'yes', 'on')

    return availability


def get_enabled_tools() -> List[str]:
    """Get list of currently enabled tools"""
    availability = get_tool_availability()
    return [tool for tool, enabled in availability.items() if enabled]


def is_tool_enabled(tool_name: str) -> bool:
    """Check if a specific tool is enabled"""
    availability = get_tool_availability()
    return availability.get(tool_name, False)


def get_tool_description(tool_name: str) -> str:
    """Get description for a specific tool"""
    return TOOL_DESCRIPTIONS.get(tool_name, f"{tool_name} tool")


def get_tool_category(tool_name: str) -> str:
    """Get category for a specific tool"""
    return TOOL_CATEGORIES.get(tool_name, "Other")


# Development mode settings
class ToolConfig:
    """Tool configuration class for easy management"""

    @staticmethod
    def disable_all_tools():
        """Disable all tools (useful for testing)"""
        global TOOL_AVAILABILITY
        TOOL_AVAILABILITY = {tool: False for tool in TOOL_AVAILABILITY}

    @staticmethod
    def enable_all_tools():
        """Enable all tools"""
        global TOOL_AVAILABILITY
        TOOL_AVAILABILITY = {tool: True for tool in TOOL_AVAILABILITY}

    @staticmethod
    def set_tool_enabled(tool_name: str, enabled: bool):
        """Enable or disable a specific tool"""
        if tool_name in TOOL_AVAILABILITY:
            TOOL_AVAILABILITY[tool_name] = enabled

    @staticmethod
    def get_available_tools_info() -> Dict[str, Dict[str, str]]:
        """Get comprehensive info about all available tools"""
        availability = get_tool_availability()
        return {
            tool: {
                "enabled": availability.get(tool, False),
                "description": get_tool_description(tool),
                "category": get_tool_category(tool),
            }
            for tool in TOOL_DESCRIPTIONS
        }

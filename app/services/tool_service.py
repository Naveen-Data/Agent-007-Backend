from typing import Any, Dict, Optional

from app.core.interfaces import ToolResult
from app.tools_config import (
    get_tool_availability,
    is_tool_enabled,
    get_tool_description,
)
from app.logging_config import get_logger

from app.tools.github_issues import GitHubIssuesTool
from app.tools.http_tool import HttpTool
from app.tools.vector_query import VectorQueryTool
from app.tools.weather import WeatherTool
from app.tools.web_search import WebSearchTool

logger = get_logger("app.tools")


class ToolService:
    """Implements each tool callable via MCP."""

    def __init__(self):
        # Initialize all available tools
        all_tools = {
            "web_search": WebSearchTool(),
            "vector_query": VectorQueryTool(),
            "github_issues": GitHubIssuesTool(),
            "weather": WeatherTool(),
            "http_tool": HttpTool(),
        }

        # Filter tools based on configuration
        tool_availability = get_tool_availability()
        self.tools = {
            name: tool
            for name, tool in all_tools.items()
            if tool_availability.get(name, False)
        }

        enabled_tools = list(self.tools.keys())
        disabled_tools = [name for name in all_tools if name not in self.tools]

        logger.info(
            "ToolService initialized",
            extra={
                'enabled_tools': enabled_tools,
                'disabled_tools': disabled_tools,
                'total_available': len(all_tools),
            },
        )

    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools and their descriptions"""
        return {name: get_tool_description(name) for name in self.tools.keys()}

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute the specified tool with given parameters.

        Returns a plain string for backward compatibility even though the
        underlying tool returns a `ToolResult`.
        """
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            return f"Unknown tool '{tool_name}'. Available tools: {available}"

        tool = self.tools[tool_name]
        try:
            result = tool.run(**kwargs)
            if isinstance(result, ToolResult):
                if result.success:
                    return result.output or ""
                return f"Tool error: {result.error}"
            # Fallback if a tool still returns raw string
            return str(result)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool instance"""
        return self.tools.get(tool_name)

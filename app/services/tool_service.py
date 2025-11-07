from typing import Dict, Any, Optional
from app.tools.web_search import WebSearchTool
from app.tools.vector_query import VectorQueryTool
from app.tools.github_issues import GitHubIssuesTool
from app.tools.weather import WeatherTool
from app.tools.http_tool import HttpTool

class ToolService:
    """Implements each tool callable via MCP."""
    
    def __init__(self):
        self.tools = {
            "web_search": WebSearchTool(),
            "vector_query": VectorQueryTool(),
            "github_issues": GitHubIssuesTool(),
            "weather": WeatherTool(),
            "http_tool": HttpTool()
        }
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools and their descriptions"""
        return {name: tool.description for name, tool in self.tools.items()}
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute the specified tool with given parameters"""
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            return f"Unknown tool '{tool_name}'. Available tools: {available}"
        
        try:
            tool = self.tools[tool_name]
            return tool._run(**kwargs)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool instance"""
        return self.tools.get(tool_name)
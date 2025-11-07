"""Tool discovery and initialization."""
from .web_search import WebSearchTool
from .vector_query import VectorQueryTool
from .github_issues import GitHubIssuesTool
from .weather import WeatherTool
from .http_tool import HttpTool
from .base import ToolSpec

__all__ = [
    "WebSearchTool",
    "VectorQueryTool", 
    "GitHubIssuesTool",
    "WeatherTool",
    "HttpTool",
    "ToolSpec"
]
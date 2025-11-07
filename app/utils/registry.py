from typing import Dict, Any, List
from app.tools.base import ToolSpec

class ToolRegistry:
    """Tool discovery and registration logic."""
    
    def __init__(self):
        self.tools: Dict[str, ToolSpec] = {}
        self.tool_descriptions: Dict[str, str] = {}
    
    def register_tool(self, tool_name: str, tool_instance: ToolSpec):
        """Register a tool with the registry"""
        if not isinstance(tool_instance, ToolSpec):
            raise ValueError(f"Tool must be an instance of ToolSpec, got {type(tool_instance)}")
        
        self.tools[tool_name] = tool_instance
        self.tool_descriptions[tool_name] = tool_instance.description
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool from the registry"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            del self.tool_descriptions[tool_name]
    
    def get_tool(self, tool_name: str) -> ToolSpec:
        """Get a registered tool by name"""
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        return self.tools[tool_name]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all registered tools"""
        return self.tool_descriptions.copy()
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a registered tool with given parameters"""
        tool = self.get_tool(tool_name)
        return tool._run(**kwargs)

# Global tool registry instance
tool_registry = ToolRegistry()
from abc import ABC, abstractmethod
from typing import Any, Dict

class ToolSpec(ABC):
    """Base class for all tools in the system"""
    
    def __init__(self):
        self.name: str = "base_tool"
        self.description: str = "Base tool class"
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """Execute the tool with given parameters"""
        raise NotImplementedError
    
    def run(self, *args, **kwargs) -> str:
        """Public interface to run the tool"""
        return self._run(*args, **kwargs)

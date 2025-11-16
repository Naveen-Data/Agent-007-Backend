from abc import ABC, abstractmethod
from typing import Any

from app.core.interfaces import ToolInterface, ToolResult


class ToolSpec(ToolInterface, ABC):
    """Base class for all tools in the system.

    Concrete tools should implement `_run` returning a string (legacy behavior).
    The public `run` method wraps that into a `ToolResult` for standardized
    downstream consumption.
    """

    def __init__(self):
        self.name: str = "base_tool"
        self.description: str = "Base tool class"

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def run(self, *args, **kwargs) -> ToolResult:
        try:
            output = self._run(*args, **kwargs)
            return ToolResult(success=True, output=output)
        except Exception as e:  # pragma: no cover - defensive
            return ToolResult(success=False, error=str(e))

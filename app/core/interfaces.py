from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool = True
    output: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LLMInterface(ABC):
    """Abstract interface for LLM adapters.

    Keep methods minimal — implementations may be sync or async. Services
    using these should call them via adapters or helper wrappers.
    """

    @abstractmethod
    async def generate(
        self, prompt: str, **kwargs
    ) -> str:  # async to support non-blocking implementations
        raise NotImplementedError()

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        raise NotImplementedError()


class ToolInterface(ABC):
    """Minimal tool interface used by the ToolService/AgentService."""

    @abstractmethod
    def run(self, input: str, **kwargs) -> ToolResult:
        raise NotImplementedError()


class VectorStoreInterface(ABC):
    """Abstract vector store interface used by services for retrieval.

    Keep operations minimal to ease adapters for Chroma, FAISS, or remote
    vector stores.
    """

    @abstractmethod
    def query(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    def upsert(self, docs: List[Dict[str, Any]]) -> None:
        raise NotImplementedError()

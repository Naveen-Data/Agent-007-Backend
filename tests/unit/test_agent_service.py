import asyncio
from typing import List

import pytest

from app.services.agent_service import AgentService
from app.core.interfaces import LLMInterface, VectorStoreInterface, ToolResult, ToolInterface


class MockLLM(LLMInterface):
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"LLM:{prompt.splitlines()[0][:40]}"
    
    async def generate_structured(self, prompt: str, response_model, **kwargs):
        """Mock structured generation for testing"""
        from app.models import GeneralResponse, RAGResponse, ToolSelection
        
        if response_model == GeneralResponse:
            return GeneralResponse(response="Mock structured response")
        elif response_model == RAGResponse:
            return RAGResponse(
                answer="Mock RAG answer",
                sources_used=["source1"],
                context_relevance=0.8
            )
        elif response_model == ToolSelection:
            return ToolSelection(
                selected_tool="dummy",
                parameters={"input": "test"},
                reasoning="Mock tool selection"
            )
        return None

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Fix signature to match interface expectation"""
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeDoc:
    def __init__(self, content: str):
        self.page_content = content
        self.metadata = {"source": "test"}


class MockRetriever:
    def invoke(self, query: str):
        return [FakeDoc(f"Answer about {query}")]


class MockVectorStore(VectorStoreInterface):
    def query(self, query: str, k: int = 4):  # type: ignore[override]
        return [{"text": f"Doc for {query}"}]

    def upsert(self, docs):  # type: ignore[override]
        return None

    # Provide invoke to mimic retriever behavior used by AgentService
    def invoke(self, query: str):
        return [FakeDoc(f"VS doc for {query}")]


class DummyTool(ToolInterface):
    def run(self, input: str, **kwargs) -> ToolResult:  # type: ignore[override]
        return ToolResult(success=True, output=f"TOOL:{input}")


@pytest.mark.asyncio
async def test_agent_service_rag_mode(monkeypatch):
    # Patch get_retriever to avoid real vectorstore initialization
    from app import vectorstore as vs_module

    monkeypatch.setattr(vs_module, "get_retriever", lambda k=4: MockRetriever())

    from app.constants import AgentConstants
    agent = AgentService(mode=AgentConstants.MODE_RAG, llm=MockLLM())
    reply = await agent.answer_with_history("test question", [])
    assert "Mock" in reply


@pytest.mark.asyncio
async def test_agent_service_tools_mode(monkeypatch):
    # Provide a ToolService override via monkeypatch on registry
    from app.services import tool_service as tool_module
    from app.constants import AgentConstants

    class MockToolService(tool_module.ToolService):
        def __init__(self):
            super().__init__()
            self.tools = {"dummy": DummyTool()}

        def get_available_tools(self):  # override for simplicity
            return {"dummy": "Dummy tool"}

        def execute_tool(self, tool_name: str, **kwargs) -> str:  # returns string
            if tool_name == "dummy":
                return self.tools[tool_name].run(kwargs.get("input", "")).output or ""
            return "unknown tool"

    tool_service_instance = MockToolService()
    agent = AgentService(mode=AgentConstants.MODE_TOOLS, llm=MockLLM(), tool_service=tool_service_instance)

    reply = await agent.answer_with_history("use tool to echo hello", [])
    # Should produce a structured response or fallback
    assert "Mock" in reply or "LLM:" in reply


@pytest.mark.asyncio
async def test_agent_service_chat_mode():
    """Test chat mode (default conversational mode)"""
    from app.constants import AgentConstants
    agent = AgentService(mode=AgentConstants.MODE_CHAT, llm=MockLLM())
    reply = await agent.answer_with_history("Hello, how are you?", [])
    assert "Mock" in reply


@pytest.mark.asyncio
async def test_agent_service_expressive_mode(monkeypatch):
    """Test expressive mode with heavy model"""
    from app.constants import AgentConstants
    from app.services import llm_service as llm_module
    
    # Mock the LLMService constructor to return our MockLLM
    def mock_llm_service(*args, **kwargs):
        return MockLLM()
    
    monkeypatch.setattr(llm_module, "LLMService", mock_llm_service)
    
    agent = AgentService(mode=AgentConstants.MODE_EXPRESSIVE, llm=MockLLM())
    reply = await agent.answer_with_history("Explain quantum physics in detail", [])
    assert reply is not None and len(reply) > 0


@pytest.mark.asyncio
async def test_agent_service_enhanced_tools_mode():
    """Test enhanced tools mode with advanced capabilities"""
    from app.services import tool_service as tool_module
    from app.constants import AgentConstants
    
    class MockEnhancedToolService(tool_module.ToolService):
        def __init__(self):
            super().__init__()
            self.tools = {"advanced_dummy": DummyTool()}

        def get_available_tools(self):
            return {"advanced_dummy": "Advanced dummy tool"}

        def execute_tool(self, tool_name: str, **kwargs) -> str:
            if tool_name == "advanced_dummy":
                return self.tools[tool_name].run(kwargs.get("input", "")).output or ""
            return "unknown tool"

    tool_service_instance = MockEnhancedToolService()
    agent = AgentService(
        mode=AgentConstants.MODE_ENHANCED_TOOLS, 
        llm=MockLLM(), 
        tool_service=tool_service_instance
    )
    
    reply = await agent.answer_with_history("Use advanced analysis tools", [])
    assert reply is not None and len(reply) > 0  # Could be mock or real response


@pytest.mark.asyncio
async def test_agent_service_with_conversation_history():
    """Test agent service with conversation history"""
    from app.constants import AgentConstants
    
    # Mock conversation history
    class MockMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content
    
    history = [
        MockMessage("user", "What is Python?"),
        MockMessage("assistant", "Python is a programming language.")
    ]
    
    agent = AgentService(mode=AgentConstants.MODE_CHAT, llm=MockLLM())
    reply = await agent.answer_with_history("Tell me more about it", history)
    assert "Mock" in reply


@pytest.mark.asyncio
async def test_agent_service_error_handling():
    """Test error handling in agent service"""
    from app.constants import AgentConstants
    
    class FailingLLM(LLMInterface):
        async def generate(self, prompt: str, **kwargs) -> str:
            raise Exception("LLM Error")
        
        async def generate_structured(self, prompt: str, response_model, **kwargs):
            raise Exception("Structured generation failed")
        
        def embed(self, texts: List[str]) -> List[List[float]]:
            raise Exception("Embedding failed")
    
    agent = AgentService(mode=AgentConstants.MODE_CHAT, llm=FailingLLM())
    
    # Test that errors are properly propagated
    with pytest.raises(Exception):
        await agent.answer_with_history("This should fail", [])


@pytest.mark.asyncio
async def test_all_agent_modes_initialization():
    """Test that all agent modes can be initialized"""
    from app.constants import AgentConstants
    
    modes = [
        AgentConstants.MODE_RAG,
        AgentConstants.MODE_TOOLS,
        AgentConstants.MODE_CHAT,
        AgentConstants.MODE_EXPRESSIVE,
        AgentConstants.MODE_ENHANCED_TOOLS
    ]
    
    for mode in modes:
        agent = AgentService(mode=mode, llm=MockLLM())
        assert agent.mode == mode
        assert agent.llm is not None

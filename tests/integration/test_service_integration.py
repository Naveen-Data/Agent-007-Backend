"""
Integration Tests for Services

Tests for interactions between different services and components.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.agent_service import AgentService
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService


class TestAgentServiceIntegration:
    """Test agent service integration with other components"""
    
    def test_agent_service_with_tool_service_integration(self):
        """Test agent service integrates properly with tool service"""
        from app.constants import AgentConstants
        
        # Create agent with tools mode
        agent = AgentService(mode=AgentConstants.MODE_TOOLS)
        
        # Verify tool service is properly integrated
        assert agent.tool_service is not None
        assert isinstance(agent.tool_service, ToolService)
        
        # Verify tools are available
        tools = agent.tool_service.get_available_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0
        
    def test_agent_service_with_llm_integration(self):
        """Test agent service integrates properly with LLM service"""
        from app.constants import AgentConstants
        
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        # Verify LLM service is properly integrated
        assert agent.llm is not None
        assert hasattr(agent.llm, 'generate')
        assert hasattr(agent.llm, 'generate_structured')
        
    @pytest.mark.asyncio
    async def test_agent_with_mocked_services(self):
        """Test agent service with mocked dependencies"""
        from app.constants import AgentConstants
        from unittest.mock import AsyncMock
        
        # Create mock services with proper async support
        mock_llm = Mock()
        mock_response = Mock(response="Integration test response")
        mock_llm.generate_structured = AsyncMock(return_value=mock_response)
        
        mock_tool_service = Mock()
        mock_tool_service.get_available_tools.return_value = {"test_tool": "Test tool"}
        
        # Create agent with mocked dependencies
        agent = AgentService(
            mode=AgentConstants.MODE_CHAT,
            llm=mock_llm,
            tool_service=mock_tool_service
        )
        
        # Test that agent uses the provided dependencies
        assert agent.llm is mock_llm
        assert agent.tool_service is mock_tool_service
        
        # Test conversation flow
        result = await agent.answer_with_history("Test question", [])
        
        # Verify the mock was called and result is correct
        mock_llm.generate_structured.assert_called_once()
        assert "Integration test response" in result


class TestServiceConfiguration:
    """Test service configuration and dependency injection"""
    
    def test_agent_service_dependency_injection(self):
        """Test that agent service accepts injected dependencies"""
        from app.constants import AgentConstants
        
        # Create custom implementations
        custom_llm = Mock()
        custom_tool_service = Mock()
        
        agent = AgentService(
            mode=AgentConstants.MODE_CHAT,
            llm=custom_llm,
            tool_service=custom_tool_service
        )
        
        # Verify injection worked
        assert agent.llm is custom_llm
        assert agent.tool_service is custom_tool_service
        
    def test_agent_service_fallback_defaults(self):
        """Test that agent service falls back to defaults when no dependencies provided"""
        from app.constants import AgentConstants
        
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        # Should have default implementations
        assert agent.llm is not None
        assert agent.tool_service is not None
        assert isinstance(agent.tool_service, ToolService)
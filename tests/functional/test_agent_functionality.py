"""
Functional Tests for Agent System

End-to-end tests for complete agent functionality.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.agent_service import AgentService
from app.constants import AgentConstants


class TestAgentFunctionality:
    """Test complete agent functionality end-to-end"""
    
    @pytest.mark.asyncio
    async def test_chat_mode_functionality(self):
        """Test complete chat mode functionality"""
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        # Mock the LLM to return a predictable response
        with patch.object(agent.llm, 'generate_structured') as mock_generate:
            mock_response = Mock()
            mock_response.response = "This is a chat response"
            mock_generate.return_value = mock_response
            
            result = await agent.answer_with_history("Hello", [])
            
            assert result is not None
            assert "This is a chat response" in result
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_expressive_mode_functionality(self):
        """Test complete expressive mode functionality"""
        agent = AgentService(mode=AgentConstants.MODE_EXPRESSIVE)
        
        # Test with a simple question to get a real response
        result = await agent.answer_with_history("What is AI?", [])
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 50  # Should be a substantial response
        # Expressive mode should provide detailed responses
        assert "AI" in result or "artificial intelligence" in result.lower()
    
    @pytest.mark.asyncio
    async def test_enhanced_tools_mode_functionality(self):
        """Test complete enhanced tools mode functionality"""
        agent = AgentService(mode=AgentConstants.MODE_ENHANCED_TOOLS)
        
        # Test with a general question
        result = await agent.answer_with_history("What can you help me with?", [])
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 50  # Should be a substantial response
        # Enhanced tools mode should mention capabilities or analysis
        assert any(word in result.lower() for word in ["agent", "analysis", "help", "assist", "007"])


class TestAgentModeComparison:
    """Test different agent modes produce appropriate responses"""
    
    def test_mode_differences(self):
        """Test that different modes are properly configured"""
        chat_agent = AgentService(mode=AgentConstants.MODE_CHAT)
        expressive_agent = AgentService(mode=AgentConstants.MODE_EXPRESSIVE)
        tools_agent = AgentService(mode=AgentConstants.MODE_ENHANCED_TOOLS)
        
        # Verify they have different modes
        assert chat_agent.mode != expressive_agent.mode
        assert chat_agent.mode != tools_agent.mode
        assert expressive_agent.mode != tools_agent.mode
        
        # Verify mode constants are properly set
        assert chat_agent.mode == AgentConstants.MODE_CHAT
        assert expressive_agent.mode == AgentConstants.MODE_EXPRESSIVE
        assert tools_agent.mode == AgentConstants.MODE_ENHANCED_TOOLS


class TestAgentErrorHandling:
    """Test agent error handling in various scenarios"""
    
    @pytest.mark.asyncio
    async def test_llm_service_error_handling(self):
        """Test agent handles LLM service errors gracefully"""
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        # Mock LLM to raise an exception
        with patch.object(agent.llm, 'generate_structured') as mock_generate:
            mock_generate.side_effect = Exception("LLM service error")
            
            # Agent should raise the error for proper exception handling
            with pytest.raises(Exception, match="LLM service error"):
                await agent.answer_with_history("Test question", [])
    
    @pytest.mark.asyncio
    async def test_empty_input_handling(self):
        """Test agent handles empty input appropriately"""
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        with patch.object(agent.llm, 'generate_structured') as mock_generate:
            mock_response = Mock()
            mock_response.response = "Please provide a question or message"
            mock_generate.return_value = mock_response
            
            result = await agent.answer_with_history("", [])
            
            assert result is not None
            mock_generate.assert_called_once()


class TestAgentPerformance:
    """Test agent performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_time_reasonable(self):
        """Test that agent responds within reasonable time"""
        import time
        
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        
        with patch.object(agent.llm, 'generate_structured') as mock_generate:
            mock_response = Mock()
            mock_response.response = "Quick response"
            mock_generate.return_value = mock_response
            
            start_time = time.time()
            result = await agent.answer_with_history("Quick question", [])
            end_time = time.time()
            
            # Should respond quickly with mocked LLM
            response_time = end_time - start_time
            assert response_time < 1.0  # Should be very fast with mock
            assert result is not None
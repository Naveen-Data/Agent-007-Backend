"""
Smoke Tests for Basic System Health

Quick tests to verify system is operational.
"""

import pytest


class TestSystemHealth:
    """Basic system health checks"""
    
    def test_imports(self):
        """Test that core modules can be imported"""
        try:
            import app.main  # noqa
            import app.services.agent_service  # noqa
            import app.services.llm_service  # noqa
            import app.services.tool_service  # noqa
            import app.models  # noqa
            import app.constants  # noqa
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
        
        assert True
    
    def test_constants_available(self):
        """Test that constants are properly defined"""
        from app.constants import AgentConstants
        
        assert hasattr(AgentConstants, 'MODE_CHAT')
        assert hasattr(AgentConstants, 'MODE_EXPRESSIVE')
        assert hasattr(AgentConstants, 'MODE_ENHANCED_TOOLS')
        
        # Verify default mode is set
        assert AgentConstants.MODE_CHAT == "chat"
    
    def test_agent_service_instantiation(self):
        """Test that agent service can be instantiated"""
        from app.services.agent_service import AgentService
        from app.constants import AgentConstants
        
        # Should be able to create agent without errors
        agent = AgentService(mode=AgentConstants.MODE_CHAT)
        assert agent is not None
        assert agent.mode == AgentConstants.MODE_CHAT
    
    def test_models_importable(self):
        """Test that Pydantic models are properly defined"""
        from app.models import GeneralResponse, RAGResponse
        
        # Should be able to create model instances
        response = GeneralResponse(response="test response")
        assert response.response == "test response"
        
        rag_response = RAGResponse(
            answer="test answer",
            context_relevance=0.8,
            sources_used=["source1"]
        )
        assert rag_response.answer == "test answer"
        assert rag_response.context_relevance == 0.8
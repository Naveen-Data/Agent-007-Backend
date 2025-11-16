"""
Basic Import and Health Check Tests

Tests for basic application functionality and import validation.
"""

import pytest
from app.main import app, health


class TestBasicImports:
    """Test that all core modules can be imported without errors"""
    
    def test_import_main_app(self):
        """Test that the main FastAPI app can be imported"""
        assert app is not None
        
    def test_import_services(self):
        """Test that all services can be imported"""
        from app.services.agent_service import AgentService
        from app.services.llm_service import LLMService
        from app.services.tool_service import ToolService
        
        assert AgentService is not None
        assert LLMService is not None
        assert ToolService is not None
        
    def test_import_tools(self):
        """Test that all tools can be imported"""
        from app.tools.weather import WeatherTool
        from app.tools.web_search import WebSearchTool
        from app.tools.vector_query import VectorQueryTool
        
        assert WeatherTool is not None
        assert WebSearchTool is not None
        assert VectorQueryTool is not None

    def test_import_constants(self):
        """Test that constants can be imported"""
        from app.constants import AgentConstants
        assert AgentConstants is not None


class TestHealthCheck:
    """Test health check functionality"""
    
    def test_health_endpoint_structure(self):
        """Test that health check function works"""
        result = health()
        assert result["status"] == "ok"
        assert "timestamp" in result  # Health endpoint includes timestamp
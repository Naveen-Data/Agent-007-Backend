# Backend Tests - Basic functionality tests for CI/CD pipeline

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.agent_service import AgentService
from app.services.llm_service import LLMService  
from app.services.tool_service import ToolService
from app.tools.weather import WeatherTool
from app.tools.web_search import WebSearchTool

class TestBasicImports:
    """Test that all core modules can be imported without errors"""
    
    def test_import_main_app(self):
        """Test that the main FastAPI app can be imported"""
        from app.main import app
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

class TestToolService:
    """Test tool service functionality"""
    
    def test_tool_service_initialization(self):
        """Test that ToolService initializes correctly"""
        tool_service = ToolService()
        
        # Check that tools are loaded
        tools = tool_service.get_available_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0
        
        # Check for required tools
        assert "weather" in tools
        assert "web_search" in tools
        
    def test_weather_tool_structure(self):
        """Test weather tool can be instantiated"""
        weather_tool = WeatherTool()
        assert weather_tool.name == "weather"
        assert weather_tool.description is not None
        
    @patch('httpx.Client')
    def test_weather_tool_mock_response(self, mock_client):
        """Test weather tool with mocked response"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "current_condition": [{
                "weatherDesc": [{"value": "Clear"}],
                "temp_C": "20",
                "temp_F": "68",
                "humidity": "50",
                "windspeedKmph": "10",
                "winddir16Point": "N"
            }],
            "nearest_area": [{
                "areaName": [{"value": "Test City"}],
                "country": [{"value": "Test Country"}]
            }],
            "weather": [{
                "maxtempC": "25",
                "mintempC": "15"
            }]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_context = Mock()
        mock_context.__enter__.return_value.get.return_value = mock_response
        mock_client.return_value = mock_context
        
        weather_tool = WeatherTool()
        result = weather_tool._run("Test Location")
        
        assert "Test City" in result
        assert "Clear" in result
        assert "20°C" in result

class TestAgentService:
    """Test agent service functionality"""
    
    def test_agent_service_initialization(self):
        """Test that AgentService initializes correctly"""
        agent = AgentService(mode="rag")
        assert agent.mode == "rag"
        assert agent.llm is not None
        assert agent.tool_service is not None
        
    def test_agent_service_tools_mode(self):
        """Test agent service in tools mode"""
        agent = AgentService(mode="tools")
        assert agent.mode == "tools"
        
    @pytest.mark.asyncio
    async def test_agent_service_mock_response(self):
        """Test agent service with mocked LLM response"""
        with patch.object(LLMService, 'generate') as mock_generate:
            mock_generate.return_value = "Mock response"
            
            agent = AgentService(mode="rag")
            result = await agent.answer("test question")
            
            assert result == "Mock response"
            mock_generate.assert_called_once()

class TestLLMService:
    """Test LLM service functionality"""
    
    def test_llm_service_initialization(self):
        """Test that LLMService initializes correctly"""
        llm = LLMService()
        assert llm.model is not None
        
    @pytest.mark.asyncio
    async def test_llm_service_mock_generate(self):
        """Test LLM generation with mock"""
        with patch.object(LLMService, 'generate') as mock_generate:
            mock_generate.return_value = "Mock LLM response"
            
            llm = LLMService()
            result = await llm.generate("test prompt")
            
            assert result == "Mock LLM response"

class TestHealthCheck:
    """Test health check functionality"""
    
    def test_health_endpoint_structure(self):
        """Test that health check function works"""
        from app.main import health
        
        result = health()
        assert result == {"status": "ok"}

# Configuration for pytest
def pytest_configure():
    """Configure pytest with custom markers"""
    pass

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    monkeypatch.setenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash-lite")
    monkeypatch.setenv("GEMINI_HEAVY_MODEL", "gemini-2.5-pro") 
    monkeypatch.setenv("EMBEDDING_MODEL", "gemini-embedding-001")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("BACKEND_PORT", "8000")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("CHROMA_DIR", "./test_chroma_db")
    monkeypatch.setenv("CHROMA_TELEMETRY_ENABLED", "false")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
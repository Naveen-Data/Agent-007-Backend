"""
Tool Service Unit Tests

Tests for individual tools and the tool service.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.tool_service import ToolService
from app.tools.weather import WeatherTool
from app.tools.web_search import WebSearchTool


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
        
    def test_tool_service_execute_tool(self):
        """Test tool execution"""
        tool_service = ToolService()
        
        # Test with a simple tool that should exist
        tools = tool_service.get_available_tools()
        if "weather" in tools:
            # Mock the actual tool execution to avoid API calls
            with patch.object(WeatherTool, '_run') as mock_run:
                mock_run.return_value = "Mocked weather result"
                
                result = tool_service.execute_tool("weather", location="Test City")
                assert "Mocked weather result" in result


class TestWeatherTool:
    """Test weather tool functionality"""
    
    def test_weather_tool_structure(self):
        """Test weather tool can be instantiated"""
        weather_tool = WeatherTool()
        assert weather_tool.name == "weather"
        assert weather_tool.description is not None
        
    @patch("app.tools.weather.httpx.request")
    def test_weather_tool_mock_response(self, mock_request):
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

        # Make httpx.request(...) return the mocked response
        mock_request.return_value = mock_response

        weather_tool = WeatherTool()
        result = weather_tool._run("Test Location")

        assert "Test City" in result
        assert "Clear" in result
        assert "20°C" in result


class TestWebSearchTool:
    """Test web search tool functionality"""
    
    def test_web_search_tool_structure(self):
        """Test web search tool can be instantiated"""
        web_search_tool = WebSearchTool()
        assert web_search_tool.name == "web_search"
        assert web_search_tool.description is not None
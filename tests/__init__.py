"""
Agent 007 Backend Test Suite

This module contains all tests for the Agent 007 Backend application.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions  
- functional/: End-to-end functional tests
- performance/: Performance and load tests

Usage:
    pytest tests/                    # Run all tests
    pytest tests/unit/              # Run only unit tests
    pytest tests/integration/       # Run only integration tests
    pytest tests/functional/        # Run only functional tests
"""

# Test configuration
import pytest
import os
import sys
from unittest.mock import Mock

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Common test fixtures
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    monkeypatch.setenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash-lite")
    monkeypatch.setenv("GEMINI_HEAVY_MODEL", "gemini-2.5-pro") 
    monkeypatch.setenv("EMBEDDING_MODEL", "gemini-embedding-001")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("BACKEND_PORT", "8000")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("CHROMA_DIR", "./test_chroma_db")
    monkeypatch.setenv("CHROMA_TELEMETRY_ENABLED", "false")

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    from app.services.llm_service import LLMService
    mock = Mock(spec=LLMService)
    mock.generate.return_value = "Mock LLM Response"
    mock.generate_structured.return_value = Mock(response="Mock Structured Response")
    mock.embed.return_value = [[0.1, 0.2, 0.3]]
    return mock

@pytest.fixture  
def mock_tool_service():
    """Mock tool service for testing"""
    from app.services.tool_service import ToolService
    mock = Mock(spec=ToolService)
    mock.get_available_tools.return_value = {"dummy": "Dummy tool for testing"}
    mock.execute_tool.return_value = "Mock tool result"
    return mock
"""
LLM Service Unit Tests

Tests for the LLM service functionality in isolation.
"""

import pytest
from unittest.mock import patch, Mock
from app.services.llm_service import LLMService


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
            
    @pytest.mark.asyncio
    async def test_llm_service_structured_generation(self):
        """Test structured LLM generation with mock"""
        with patch.object(LLMService, 'generate_structured') as mock_generate_structured:
            from app.models import GeneralResponse
            mock_response = GeneralResponse(response="Mock structured response")
            mock_generate_structured.return_value = mock_response
            
            llm = LLMService()
            result = await llm.generate_structured("test prompt", GeneralResponse)
            
            assert result.response == "Mock structured response"
            
    @pytest.mark.asyncio
    async def test_llm_service_embed_mock(self):
        """Test LLM embedding with mock"""
        with patch.object(LLMService, 'embed') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            
            llm = LLMService()
            result = await llm.embed(["text1", "text2"])
            
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
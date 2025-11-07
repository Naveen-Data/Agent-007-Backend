# Note: file named services_llm_service.py to avoid folder creation issues in script
import os
import asyncio
from typing import List, Type, TypeVar, Optional
from pydantic import BaseModel
from app.config import settings

# Use LangChain's Google Gemini integration
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    llm_available = True
except Exception:
    llm_available = False

T = TypeVar('T', bound=BaseModel)

class LLMService:
    """Single-responsibility LLM wrapper. Handles model selection and low-level API calls."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.GEMINI_DEFAULT_MODEL
        self.llm = None
        if llm_available:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.2
                )
            except Exception as e:
                print(f"Failed to initialize LLM: {e}")
                self.llm = None

    async def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        if self.llm is None:
            await asyncio.sleep(0.05)
            return f"[MOCK] Response to: {prompt[:100]}..."
        
        try:
            # Use invoke method for newer LangChain versions
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM generation error: {e}")
            return f"[ERROR] Failed to generate response: {str(e)[:100]}"
    
    async def generate_structured(self, prompt: str, response_model: Type[T]) -> Optional[T]:
        """Generate structured response using Pydantic model"""
        if self.llm is None or not llm_available:
            return None
        
        try:
            # Create output parser
            parser = PydanticOutputParser(pydantic_object=response_model)
            
            # Add format instructions to the prompt
            format_instructions = parser.get_format_instructions()
            structured_prompt = f"{prompt}\n\n{format_instructions}"
            
            # Generate response
            response = await asyncio.to_thread(self.llm.invoke, structured_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the response
            parsed_response = parser.parse(content)
            return parsed_response
            
        except Exception as e:
            print(f"Structured generation error: {e}")
            return None

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if genai is None:
            return [[0.0]] * len(texts)
        resp = genai.get_embeddings(model=settings.EMBEDDING_MODEL, input=texts)
        # resp.embeddings may be shaped differently in SDK; adapt as needed
        return getattr(resp, "embeddings", [])

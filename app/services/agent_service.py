from typing import Optional, Dict, Any
import logging
import os
import re
from pydantic import BaseModel, Field, ValidationError
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService
from app.vectorstore import get_retriever
from app.config import settings

logger = logging.getLogger("app.agent")

class ToolSelectionResponse(BaseModel):
    """Pydantic model for LLM tool selection response"""
    selected_tool: str = Field(..., description="The selected tool name or 'llm_only'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the selected tool")
    reasoning: str = Field(..., description="Brief explanation of why this tool was selected")
    
    class Config:
        extra = "ignore"  # Ignore extra fields from LLM response

class AgentService:
    """High-level agent orchestration. Single responsibility: orchestrate chains and tools."""

    def __init__(self, mode: str = "rag"):
        self.mode = mode
        self.llm = LLMService()
        self.tool_service = ToolService()

    async def answer(self, question: str) -> str:
        # RAG mode: retrieve -> format -> LLM
        if self.mode == "rag":
            try:
                retriever = get_retriever()
                # Use invoke method for newer LangChain versions
                docs = retriever.invoke(question) if retriever else []
                context = "\n\n".join([d.page_content for d in docs[:4]])
                prompt = f"You are an assistant. Context:\n{context}\nUser: {question}\nAnswer:"
                return await self.llm.generate(prompt)
            except Exception as e:
                # Fallback to simple LLM call if retriever fails
                logger.warning(f"RAG retrieval failed: {e}")
                return await self.llm.generate(f"User: {question}\nAnswer:")
        elif self.mode == "tools":
            # Enhanced tools mode with multiple tool support
            return await self._handle_tools_mode(question)
        else:
            # heavy mode uses heavy model
            heavy = LLMService(model=None)
            heavy.model = os.getenv("GEMINI_HEAVY_MODEL", settings.GEMINI_HEAVY_MODEL)
            return await heavy.generate(question)
    
    async def _handle_tools_mode(self, question: str) -> str:
        """Handle tool-based questions with LLM-powered tool selection and parameter extraction"""
        
        # Get available tools
        available_tools = self.tool_service.get_available_tools()
        
        # Create tool selection prompt
        tool_selection_prompt = f"""You are an AI agent that can use various tools to help users. Analyze the user's question and determine which tool to use and what parameters to extract.

Available tools:
{self._format_tools_for_prompt(available_tools)}

User question: "{question}"

Select the most appropriate tool and extract the necessary parameters. If no specific tool is needed for a general knowledge question, use "llm_only" as the tool name."""
        
        try:
            # Get structured tool selection from LLM using Pydantic model
            tool_decision = await self.llm.generate_structured(tool_selection_prompt, ToolSelectionResponse)
            
            if tool_decision is None:
                logger.warning("Structured generation failed, falling back to context-aware LLM response")
                return await self._llm_fallback_with_context(question, available_tools)
            
            selected_tool = tool_decision.selected_tool
            parameters = tool_decision.parameters
            reasoning = tool_decision.reasoning
            
            # Execute the selected tool
            if selected_tool == "llm_only" or selected_tool not in available_tools:
                return await self._llm_fallback_with_context(question, available_tools)
            
            # Execute the tool with extracted parameters
            result = self.tool_service.execute_tool(selected_tool, **parameters)
            
            # Format the response with context
            formatted_response = f"""**Tool Used:** {selected_tool}
**Reasoning:** {reasoning}

**Result:**
{result}"""
            
            return formatted_response
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error in tool selection: {e}")
            return await self._llm_fallback_with_context(question, available_tools)
        except Exception as e:
            logger.error(f"Unexpected error in LLM tool selection: {e}")
            return await self._llm_fallback_with_context(question, available_tools)
    
    def _extract_location(self, text: str) -> str:
        """Extract location from text"""
        # Simple pattern matching for location extraction
        patterns = [
            r"weather (?:in|for|at|of) ([^?.!]+?)(?:\s+now)?(?:\?|$)",
            r"temperature (?:in|for|at|of) ([^?.!]+?)(?:\s+now)?(?:\?|$)",
            r"(?:weather|temperature) (?:of|in) ([A-Za-z\s,]+)",
            r"weather (?:of|in) ([A-Za-z\s,]+)",
            r"\b([A-Za-z\s,]+)\s+(?:weather|temperature)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common words and extra whitespace
                location = re.sub(r'\b(the|city|of|weather|temperature|now)\b', '', location, flags=re.IGNORECASE)
                location = re.sub(r'\s+', ' ', location).strip()
                if location and len(location) > 2:
                    return location
        
        # Fallback: try to extract any location-like words
        words = text.split()
        location_candidates = []
        for i, word in enumerate(words):
            if word.lower() in ['weather', 'temperature'] and i + 1 < len(words):
                # Take next 1-3 words as potential location
                potential_location = ' '.join(words[i+1:i+4])
                potential_location = re.sub(r'[^A-Za-z\s,]', '', potential_location).strip()
                if potential_location and len(potential_location) > 2:
                    location_candidates.append(potential_location)
        
        return location_candidates[0] if location_candidates else ""
    
    def _extract_github_repo(self, text: str) -> str:
        """Extract GitHub repository from text"""
        # Pattern for owner/repo format
        pattern = r"(?:github\.com/)?([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return ""
    
    def _extract_url(self, text: str) -> str:
        """Extract URL from text"""
        # Pattern for HTTP/HTTPS URLs
        pattern = r"https?://[^\s]+"
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        
        # Check for "fetch" command
        if text.lower().startswith("fetch "):
            url = text.split(" ", 1)[1].strip()
            if not url.startswith("http"):
                url = "https://" + url
            return url
        
        return ""
    
    def _format_tools_for_prompt(self, tools: dict) -> str:
        """Format available tools for LLM prompt"""
        formatted_tools = []
        
        # Tool descriptions with expected parameters
        tool_params = {
            "web_search": {"query": "search query string"},
            "weather": {"location": "city, country or location name"},
            "github_issues": {"repo": "owner/repository format", "state": "open/closed (optional)", "limit": "number of issues (optional)"},
            "http_tool": {"url": "HTTP URL", "method": "GET/POST/etc (optional)", "json": "JSON data (optional)"},
            "vector_query": {"query": "search query for knowledge base", "k": "number of results (optional)"}
        }
        
        for tool_name, description in tools.items():
            params = tool_params.get(tool_name, {})
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
            formatted_tools.append(f"- {tool_name}: {description}")
            if param_str:
                formatted_tools.append(f"  Parameters: {param_str}")
        
        return "\n".join(formatted_tools)
    
    async def _llm_fallback_with_context(self, question: str, available_tools: dict) -> str:
        """Fallback to LLM with tool context when no specific tool is selected"""
        tools_context = "Available tools: " + ", ".join(available_tools.keys())
        prompt = f"""You are Agent 007, an AI assistant with access to various tools.

{tools_context}

The user asked: "{question}"

Since no specific tool was selected or there was an error, provide a helpful response using your general knowledge. If you think a specific tool would be useful, mention it in your response.

Response:"""
        
        return await self.llm.generate(prompt)

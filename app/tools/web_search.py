import httpx
import asyncio
from typing import Dict, Any
from app.tools.base import ToolSpec

class WebSearchTool(ToolSpec):
    
    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Search the web for information using DuckDuckGo Instant Answer API"
    
    def _run(self, query: str) -> str:
        """Search the web for the given query"""
        try:
            # Use DuckDuckGo Instant Answer API (free, no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant information
                result = ""
                if data.get("Abstract"):
                    result += f"Abstract: {data['Abstract']}\n"
                    if data.get("AbstractSource"):
                        result += f"Source: {data['AbstractSource']}\n"
                
                if data.get("Answer"):
                    result += f"Answer: {data['Answer']}\n"
                    if data.get("AnswerType"):
                        result += f"Type: {data['AnswerType']}\n"
                
                if data.get("Definition"):
                    result += f"Definition: {data['Definition']}\n"
                    if data.get("DefinitionSource"):
                        result += f"Source: {data['DefinitionSource']}\n"
                
                if data.get("RelatedTopics"):
                    topics = data["RelatedTopics"][:5]  # Limit to first 5
                    if topics:
                        result += "\nRelated Topics:\n"
                        for i, topic in enumerate(topics, 1):
                            if isinstance(topic, dict) and topic.get("Text"):
                                text = topic["Text"][:150] + "..." if len(topic["Text"]) > 150 else topic["Text"]
                                result += f"{i}. {text}\n"
                
                if data.get("Results"):
                    results = data["Results"][:3]  # Limit to first 3
                    if results:
                        result += "\nWeb Results:\n"
                        for i, res in enumerate(results, 1):
                            if isinstance(res, dict) and res.get("Text"):
                                result += f"{i}. {res['Text']}\n"
                                if res.get("FirstURL"):
                                    result += f"   URL: {res['FirstURL']}\n"
                
                if result:
                    return f"Search results for '{query}':\n\n{result}"
                else:
                    return f"No detailed results found for '{query}'. This might be a broad topic - try being more specific."
                
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    async def arun(self, query: str) -> str:
        """Async version of web search"""
        return await asyncio.to_thread(self._run, query)
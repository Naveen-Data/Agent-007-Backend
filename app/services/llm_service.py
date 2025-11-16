# app/services/llm_service.py
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("app.services.llm_service")

# --- Try to import google.generativeai (genai) for direct embedding fallback ---
genai = None
try:
    import google.generativeai as genai_mod  # type: ignore

    genai = genai_mod
    try:
        # configure if key present; ignore failures (we remain defensive)
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
    except Exception as e:  # pragma: no cover - environment-specific
        logger.warning("google.generativeai.configure failed: %s", e)
except Exception:
    genai = None
    logger.debug("google.generativeai not available; embedding fallback disabled")

# --- Try to import LangChain Gemini adapter and embeddings classes ---
llm_available = False
embeddings_available = False
pydantic_parser_available = False

ChatGoogleGenerativeAI = None
GoogleGenerativeAIEmbeddings = None
PydanticOutputParser = None

try:
    # These imports can vary across langchain versions; guard them.
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    from langchain_google_genai import GoogleGenerativeAIEmbeddings  # type: ignore

    llm_available = True
    embeddings_available = True
except Exception:
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None
    llm_available = False
    embeddings_available = False

try:
    # PydanticOutputParser is in newer langchain_core/langchain; try common locations
    try:
        from langchain_core.output_parsers import PydanticOutputParser  # type: ignore
    except Exception:
        from langchain.output_parsers import PydanticOutputParser  # type: ignore

    pydantic_parser_available = True
except Exception:
    PydanticOutputParser = None
    pydantic_parser_available = False


T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Single-responsibility LLM wrapper for text generation and embeddings.

    - Uses LangChain's ChatGoogleGenerativeAI when available.
    - Falls back to mock responses if no LLM is configured (useful for CI/dev).
    - Uses Google Generative AI SDK for embeddings if LangChain embedding adapter not present.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or settings.GEMINI_DEFAULT_MODEL
        self._llm = None
        self._embeddings = None

        if llm_available and ChatGoogleGenerativeAI is not None:
            try:
                # Many LangChain adapters pick the API key from env; provide key if supported.
                # The ChatGoogleGenerativeAI initializer signature may differ by version;
                # this is wrapped to avoid hard failure.
                kwargs = {}
                # some versions accept google_api_key, some read env; we try both
                if getattr(settings, "GOOGLE_API_KEY", None):
                    kwargs["google_api_key"] = settings.GOOGLE_API_KEY
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model, temperature=0.2, **kwargs
                )
            except Exception as e:  # pragma: no cover
                logger.warning("Failed to initialize ChatGoogleGenerativeAI: %s", e)
                self._llm = None

        if embeddings_available and GoogleGenerativeAIEmbeddings is not None:
            try:
                # Pass the API key for embeddings as well
                embeddings_kwargs = {}
                if getattr(settings, "GOOGLE_API_KEY", None):
                    embeddings_kwargs["google_api_key"] = settings.GOOGLE_API_KEY
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    model=settings.EMBEDDING_MODEL, **embeddings_kwargs
                )
            except Exception as e:  # pragma: no cover
                logger.warning(
                    "Failed to initialize GoogleGenerativeAIEmbeddings: %s", e
                )
                self._embeddings = None

    # ---- Text generation ----
    async def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        """Return generated text. Requires properly configured LLM."""
        if self._llm is None:
            logger.error("LLM not configured - cannot generate text")
            raise Exception("LLM not configured")

        try:
            # Most ChatGoogleGenerativeAI objects are synchronous; run in thread to avoid blocking.
            resp = await asyncio.to_thread(self._llm.invoke, prompt)
            # normalize response content for different SDK shapes
            text = getattr(resp, "content", None)
            if text is None:
                text = getattr(resp, "text", None)
            if text is None:
                # try candidate shapes
                candidates = getattr(resp, "candidates", None)
                if (
                    candidates
                    and isinstance(candidates, (list, tuple))
                    and len(candidates) > 0
                ):
                    text = getattr(candidates[0], "content", str(candidates[0]))
            return str(text)
        except Exception as e:
            logger.exception("LLMService.generate failed: %s", e)
            return f"[ERROR] LLM call failed: {e}"

    # ---- Structured generation (Pydantic) ----
    async def generate_structured(
        self, prompt: str, response_model: Type[T], max_retries: int = 3
    ) -> Optional[T]:
        """Generate output and parse it into a Pydantic model using LangChain's PydanticOutputParser with retry logic."""
        if (
            self._llm is None
            or not pydantic_parser_available
            or PydanticOutputParser is None
        ):
            logger.error(
                "LLMService.generate_structured: required dependencies not available",
                extra={
                    'llm_available': self._llm is not None,
                    'parser_available': pydantic_parser_available,
                },
            )
            raise Exception(
                "Required dependencies for structured generation not available"
            )

        parser = PydanticOutputParser(pydantic_object=response_model)
        format_instructions = parser.get_format_instructions()

        for attempt in range(max_retries):
            try:
                # Enhanced prompt with explicit JSON requirement
                structured_prompt = f"""{prompt}

IMPORTANT: You must respond with valid JSON that matches the required schema. Do not include any additional text, explanations, or formatting outside the JSON.

{format_instructions}

Respond with valid JSON only:"""

                resp = await asyncio.to_thread(self._llm.invoke, structured_prompt)
                content = (
                    getattr(resp, "content", None)
                    or getattr(resp, "text", None)
                    or str(resp)
                ).strip()

                # Try to clean up the response if it has extra text
                content = self._extract_json_from_response(content)

                parsed = parser.parse(content)
                logger.debug(
                    f"Structured generation successful on attempt {attempt + 1}"
                )
                return parsed

            except Exception as e:
                logger.warning(
                    f"Structured generation attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt == max_retries - 1:
                    logger.exception("All structured generation attempts failed")
                    return None

        return None

    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from response that might contain extra text"""
        import json
        import re

        # First, try the content as-is
        try:
            json.loads(content)
            return content
        except:
            pass

        # Look for JSON block between { and }
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                json.loads(json_str)  # Validate
                return json_str
            except:
                pass

        # Look for code blocks with json
        code_block_match = re.search(
            r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL
        )
        if code_block_match:
            json_str = code_block_match.group(1)
            try:
                json.loads(json_str)  # Validate
                return json_str
            except:
                pass

        # Return original content if no valid JSON found
        return content

    # ---- Embeddings ----
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for the provided texts.

        Priority:
        1. Use LangChain GoogleGenerativeAIEmbeddings if available.
        2. Fallback to google.generativeai SDK get_embeddings if available.
        3. Otherwise return deterministic mock vectors.
        """
        # 1) LangChain embeddings
        if self._embeddings is not None:
            try:
                # LangChain embedding object often exposes embed_documents or similar sync method.
                # Use thread to avoid blocking.
                result = await asyncio.to_thread(
                    self._embeddings.embed_documents, texts
                )
                return result
            except Exception as e:  # pragma: no cover
                logger.warning(
                    "LangChain embeddings call failed, trying genai fallback: %s", e
                )

        # 2) google.generativeai SDK
        if genai is not None:
            try:
                resp = await asyncio.to_thread(
                    genai.get_embeddings, model=settings.EMBEDDING_MODEL, input=texts
                )
                embeddings = getattr(resp, "embeddings", None)
                if embeddings is None and isinstance(resp, dict) and "data" in resp:
                    # openai-like shape {"data":[{"embedding":[...]}]}
                    embeddings = [
                        item.get("embedding") or item.get("embeddings")
                        for item in resp["data"]
                    ]
                if embeddings is None:
                    # fallback to casting resp
                    embeddings = list(resp)
                return embeddings
            except Exception as e:
                logger.exception("genai embeddings call failed: %s", e)

        # No embeddings service available
        logger.error("No embeddings service available - cannot generate embeddings")
        raise Exception("No embeddings service available")

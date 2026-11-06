import os
import asyncio
import json
import re
from typing import TypeVar, Type
import httpx
from pydantic import BaseModel, ValidationError
from app.config import Settings
from app.core.logging import get_logger
from app.core.exceptions import LLMError, LLMTimeoutError

logger = get_logger("llm")

T = TypeVar("T", bound=BaseModel)

class LLMService:
    """Shared Ollama model service with concurrency control and structured output validation."""

    def __init__(self, settings: Settings):
        url = settings.ollama_url
        if "host.docker.internal" in url and not os.path.exists("/.dockerenv"):
            url = url.replace("host.docker.internal", "127.0.0.1")
        self.url = url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
        self._max_concurrent = settings.ollama_max_concurrent
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    async def generate(self, prompt: str, temperature: float = 0.4, system: str | None = None) -> str:
        """Call Ollama for unstructured text generation under concurrency control."""
        async with self.semaphore:
            logger.info("LLM text request started (model=%s, prompt_len=%d)", self.model, len(prompt))
            timeout = httpx.Timeout(self.timeout, connect=10.0)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_ctx": 4096},
            }
            if system:
                payload["system"] = system

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(f"{self.url}/api/generate", json=payload)
                    response.raise_for_status()
                    result = response.json().get("response", "").strip()
                    logger.info("LLM response received (len=%d)", len(result))
                    return result
            except httpx.TimeoutException as exc:
                logger.error("LLM timeout after %ss: %s", self.timeout, exc)
                raise LLMTimeoutError(f"Ollama request timed out after {self.timeout}s") from exc
            except httpx.HTTPStatusError as exc:
                logger.error("LLM HTTP error %d: %s", exc.response.status_code, exc)
                raise LLMError(f"Ollama returned HTTP {exc.response.status_code}") from exc
            except Exception as exc:
                logger.error("LLM service error: %s", exc)
                raise LLMError(str(exc)) from exc

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.2,
        system: str | None = None
    ) -> T:
        """Generate structured output validated against a Pydantic schema using Ollama's format='json'."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_instructions = (
            f"{system or 'You are an autonomous AI media specialist.'}\n\n"
            f"CRITICAL: Output strictly valid JSON matching this exact JSON Schema:\n{schema_json}\n"
            "Do NOT include markdown formatting, backticks, or preamble. Return raw JSON only."
        )

        async with self.semaphore:
            logger.info("LLM structured request started (model=%s, schema=%s)", self.model, schema.__name__)
            timeout = httpx.Timeout(self.timeout, connect=10.0)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_instructions,
                "format": "json",
                "stream": False,
                "options": {"temperature": temperature, "num_ctx": 4096},
            }

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(f"{self.url}/api/generate", json=payload)
                    response.raise_for_status()
                    raw_text = response.json().get("response", "").strip()
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(f"Ollama request timed out after {self.timeout}s") from exc
            except httpx.HTTPStatusError as exc:
                raise LLMError(f"Ollama HTTP error {exc.response.status_code}") from exc
            except Exception as exc:
                raise LLMError(str(exc)) from exc

        return self._parse_json_to_schema(raw_text, schema)

    def _parse_json_to_schema(self, text: str, schema: Type[T]) -> T:
        """Extract and validate JSON string against target Pydantic schema with heuristic repair."""
        # 1. Direct parse attempt
        try:
            return schema.model_validate_json(text)
        except ValidationError as e:
            logger.warning("Direct schema validation failed for %s: %s. Attempting extraction.", schema.__name__, e)

        # 2. Extract first matching JSON object
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                data = json.loads(candidate)
                return schema.model_validate(data)
            except Exception as sub_e:
                logger.warning("Extracted JSON candidate validation failed: %s", sub_e)

        raise LLMError(f"Failed to parse LLM response into valid {schema.__name__} schema: {text[:200]}...")

    async def health_check(self) -> dict:
        """Check if Ollama is reachable and the model is available."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.5)) as client:
                resp = await client.get(f"{self.url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                model_available = any(self.model in m for m in models)
                return {
                    "ollama": "connected",
                    "model": self.model,
                    "model_available": model_available,
                    "available_models": models,
                }
        except Exception as exc:
            return {
                "ollama": "disconnected",
                "model": self.model,
                "model_available": False,
                "error": str(exc),
            }

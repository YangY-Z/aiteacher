"""
DeepSeek (OpenAI-compatible) LLM Provider.

Uses the standard OpenAI-compatible chat completions API.
DeepSeek API: https://api.deepseek.com/v1/chat/completions
"""

import json
import logging
from typing import Any, Optional, Generator

import httpx

from app.core.exceptions import LLMServiceError
from app.services.llm_providers.base import (
    BaseLLMProvider,
    ChatCompletionResponse,
    ChatMessage,
)

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek provider implementation via OpenAI-compatible API."""

    API_BASE_URL = "https://api.deepseek.com/v1"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

    def __init__(
        self,
        api_key: str,
        default_model: str = "deepseek-chat",
        timeout: float = 60.0,
        base_url: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key.
            default_model: Default model to use (e.g. deepseek-chat, deepseek-reasoner).
            timeout: Request timeout in seconds.
            base_url: Custom base URL (defaults to https://api.deepseek.com/v1).
            max_retries: Maximum number of retries for failed requests.
        """
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout
        self._base_url = (base_url or "https://api.deepseek.com/v1").rstrip("/")
        self._max_retries = max_retries
        self._client: Optional[httpx.Client] = None

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def _http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _build_request_data(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request payload."""
        data: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": stream,
        }

        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Pass through any extra params
        if kwargs.get("extra_body"):
            data.update(kwargs["extra_body"])

        return data

    def _parse_response(self, response_data: dict[str, Any]) -> ChatCompletionResponse:
        """Parse the API response."""
        choice = response_data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")

        return ChatCompletionResponse(
            content=content,
            model=response_data.get("model", self._default_model),
            usage=response_data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )

    def chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """Send a chat completion request."""
        data = self._build_request_data(messages, model, temperature, max_tokens, **kwargs)

        logger.debug(f"[DeepSeek] Sending request to {self._base_url}/chat/completions")
        logger.debug(f"[DeepSeek] Model: {data['model']}, Messages: {len(data['messages'])}")

        try:
            response = self._http_client.post(
                self.CHAT_COMPLETIONS_ENDPOINT,
                json=data,
            )
            response.raise_for_status()
            result = response.json()
            return self._parse_response(result)

        except httpx.TimeoutException as e:
            raise LLMServiceError(
                f"DeepSeek API request timed out: {e}",
                {"provider": "deepseek"},
            )
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.text
            except Exception:
                pass
            raise LLMServiceError(
                f"DeepSeek API error ({e.response.status_code}): {error_body}",
                {"provider": "deepseek", "status_code": e.response.status_code},
            )
        except Exception as e:
            raise LLMServiceError(
                f"DeepSeek API call failed: {e}",
                {"provider": "deepseek"},
            )

    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chat completion from DeepSeek API."""
        data = self._build_request_data(messages, model, temperature, max_tokens, stream=True, **kwargs)

        logger.debug(f"[DeepSeek] Streaming request to {self._base_url}/chat/completions")

        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
            ) as client:
                with client.stream("POST", self.CHAT_COMPLETIONS_ENDPOINT, json=data) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            chunk_data = line[6:].strip()
                            if chunk_data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(chunk_data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                logger.warning(f"[DeepSeek] Failed to parse chunk: {chunk_data[:50]}")

        except httpx.TimeoutException as e:
            raise LLMServiceError(
                f"DeepSeek streaming request timed out: {e}",
                {"provider": "deepseek"},
            )
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.text
            except Exception:
                pass
            raise LLMServiceError(
                f"DeepSeek API streaming error ({e.response.status_code}): {error_body}",
                {"provider": "deepseek", "status_code": e.response.status_code},
            )
        except Exception as e:
            raise LLMServiceError(
                f"DeepSeek streaming failed: {e}",
                {"provider": "deepseek"},
            )

    def is_available(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self._api_key) and len(self._api_key) > 10

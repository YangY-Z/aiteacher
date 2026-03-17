"""Zhipu AI (智谱) LLM Provider implementation using HTTP API."""

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


class ZhipuProvider(BaseLLMProvider):
    """Zhipu AI provider implementation.

    Uses HTTP API for communication with Zhipu AI models (GLM-4, GLM-5, etc.).

    API Documentation: https://open.bigmodel.cn/dev/api
    """

    API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

    def __init__(
        self,
        api_key: str,
        default_model: str = "glm-4",
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize Zhipu AI provider.

        Args:
            api_key: Zhipu AI API key.
            default_model: Default model to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client.

        Returns:
            httpx.Client instance.
        """
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
        return self._client

    @property
    def provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name 'zhipu'.
        """
        return "zhipu"

    @property
    def default_model(self) -> str:
        """Get the default model.

        Returns:
            Default model name.
        """
        return self._default_model

    def is_available(self) -> bool:
        """Check if the provider is properly configured.

        Returns:
            True if API key is set and client can be created.
        """
        return bool(self._api_key)

    def _build_request_body(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request body for Zhipu API.

        Args:
            messages: List of chat messages.
            model: Model name.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters (e.g., thinking for GLM-5).

        Returns:
            Request body dictionary.
        """
        body: dict[str, Any] = {
            "model": model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Support for GLM-5 thinking mode
        thinking = kwargs.get("thinking")
        if thinking:
            if isinstance(thinking, bool):
                body["thinking"] = {"type": "enabled" if thinking else "disabled"}
            elif isinstance(thinking, dict):
                body["thinking"] = thinking

        # Add any other extra parameters
        for key, value in kwargs.items():
            if key not in ("thinking",) and value is not None:
                body[key] = value

        return body

    def _parse_response(
        self,
        response: httpx.Response,
        model: str,
    ) -> ChatCompletionResponse:
        """Parse the API response.

        Args:
            response: HTTP response from Zhipu API.
            model: Model name used for the request.

        Returns:
            ChatCompletionResponse instance.

        Raises:
            LLMServiceError: If response parsing fails.
        """
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMServiceError(
                f"Failed to parse Zhipu API response: {e}",
                {"response_text": response.text[:500]},
            )

        if not response.is_success:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            error_code = data.get("error", {}).get("code", "UNKNOWN")
            raise LLMServiceError(
                f"Zhipu API error: {error_msg}",
                {
                    "status_code": response.status_code,
                    "error_code": error_code,
                    "provider": "zhipu",
                },
            )

        choices = data.get("choices", [])
        if not choices:
            raise LLMServiceError(
                "Empty response from Zhipu API",
                {"response": data},
            )

        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content", "")

        usage = data.get("usage")
        finish_reason = choice.get("finish_reason")

        return ChatCompletionResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
        )

    def chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """Send chat completion request to Zhipu AI.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters (e.g., thinking=True for GLM-5).

        Returns:
            ChatCompletionResponse with the result.

        Raises:
            LLMServiceError: If the API call fails.
        """
        if not self.is_available():
            raise LLMServiceError(
                "Zhipu AI provider not configured: missing API key",
                {"provider": "zhipu"},
            )

        model = model or self._default_model
        temperature = temperature if temperature is not None else 0.7
        max_tokens = max_tokens if max_tokens is not None else 2048

        request_body = self._build_request_body(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        url = f"{self.API_BASE_URL}{self.CHAT_COMPLETIONS_ENDPOINT}"
        client = self._get_client()

        logger.debug(
            f"Sending request to Zhipu API: model={model}, messages_count={len(messages)}"
        )

        try:
            response = client.post(url, json=request_body)
            return self._parse_response(response, model)
        except httpx.TimeoutException:
            raise LLMServiceError(
                "Zhipu API request timed out",
                {
                    "timeout": self._timeout,
                    "provider": "zhipu",
                    "model": model,
                },
            )
        except httpx.RequestError as e:
            raise LLMServiceError(
                f"Zhipu API request failed: {e}",
                {"error": str(e), "provider": "zhipu"},
            )

    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chat completion request to Zhipu AI.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters.

        Yields:
            Chunks of content as they arrive.

        Raises:
            LLMServiceError: If the API call fails.
        """
        if not self.is_available():
            raise LLMServiceError(
                "Zhipu AI provider not configured: missing API key",
                {"provider": "zhipu"},
            )

        model = model or self._default_model
        temperature = temperature if temperature is not None else 0.7
        max_tokens = max_tokens if max_tokens is not None else 2048

        request_body = self._build_request_body(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        request_body["stream"] = True

        url = f"{self.API_BASE_URL}{self.CHAT_COMPLETIONS_ENDPOINT}"

        logger.debug(
            f"Sending streaming request to Zhipu API: model={model}"
        )

        try:
            with httpx.stream(
                "POST",
                url,
                json=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=self._timeout,
            ) as response:
                if not response.is_success:
                    error_text = response.read().decode()
                    raise LLMServiceError(
                        f"Zhipu API error: {error_text}",
                        {"status_code": response.status_code, "provider": "zhipu"},
                    )

                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            raise LLMServiceError(
                "Zhipu API streaming request timed out",
                {"timeout": self._timeout, "provider": "zhipu", "model": model},
            )
        except httpx.RequestError as e:
            raise LLMServiceError(
                f"Zhipu API streaming request failed: {e}",
                {"error": str(e), "provider": "zhipu"},
            )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "ZhipuProvider":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

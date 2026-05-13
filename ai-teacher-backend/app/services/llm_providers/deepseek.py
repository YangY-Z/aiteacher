"""DeepSeek LLM Provider implementation using OpenAI-compatible API."""

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
    """DeepSeek provider implementation.

    Uses OpenAI-compatible API for communication with DeepSeek models.
    
    API Documentation: https://platform.deepseek.com/api-docs/

    Features:
    - OpenAI-compatible interface
    - Supports deepseek-chat, deepseek-coder, deepseek-reasoner models
    - Streaming support
    """

    API_BASE_URL = "https://api.deepseek.com"
    CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        default_model: str = "deepseek-chat",
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key.
            default_model: Default model to use (e.g., deepseek-chat, deepseek-coder, deepseek-reasoner).
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
            Provider name 'deepseek'.
        """
        return "deepseek"

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
        """Build the request body for DeepSeek API.

        Args:
            messages: List of chat messages.
            model: Model name.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters.

        Returns:
            Request body dictionary.
        """
        body: dict[str, Any] = {
            "model": model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for key, value in kwargs.items():
            if value is not None:
                body[key] = value

        return body

    def _parse_response(
        self,
        response: httpx.Response,
        model: str,
    ) -> ChatCompletionResponse:
        """Parse the API response.

        Args:
            response: HTTP response from DeepSeek API.
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
                f"Failed to parse DeepSeek API response: {e}",
                {"response_text": response.text[:500]},
            )

        if not response.is_success:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            error_code = data.get("error", {}).get("code", "UNKNOWN")
            raise LLMServiceError(
                f"DeepSeek API error: {error_msg}",
                {
                    "status_code": response.status_code,
                    "error_code": error_code,
                    "provider": "deepseek",
                },
            )

        choices = data.get("choices", [])
        if not choices:
            raise LLMServiceError(
                "Empty response from DeepSeek API",
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
        """Send chat completion request to DeepSeek API.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters.

        Returns:
            ChatCompletionResponse with the result.

        Raises:
            LLMServiceError: If the API call fails.
        """
        if not self.is_available():
            raise LLMServiceError(
                "DeepSeek provider not configured: missing API key",
                {"provider": "deepseek"},
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

        logger.info(f"[DeepSeek] 发送请求: url={url}, model={model}, messages_count={len(messages)}")
        logger.debug(f"[DeepSeek] 请求体: {json.dumps(request_body, ensure_ascii=False)[:500]}")

        try:
            response = client.post(url, json=request_body)
            logger.info(f"[DeepSeek] 响应状态: {response.status_code}")
            
            if not response.is_success:
                logger.error(f"[DeepSeek] 请求失败: {response.text[:500]}")
            
            return self._parse_response(response, model)
        except httpx.TimeoutException:
            logger.error(f"[DeepSeek] 请求超时: timeout={self._timeout}")
            raise LLMServiceError(
                "DeepSeek API request timed out",
                {
                    "timeout": self._timeout,
                    "provider": "deepseek",
                    "model": model,
                },
            )
        except httpx.RequestError as e:
            logger.error(f"[DeepSeek] 请求错误: {e}")
            raise LLMServiceError(
                f"DeepSeek API request failed: {e}",
                {"error": str(e), "provider": "deepseek"},
            )

    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chat completion request to DeepSeek API.

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
                "DeepSeek provider not configured: missing API key",
                {"provider": "deepseek"},
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

        logger.info(f"[DeepSeek] 发送流式请求: url={url}, model={model}")
        logger.debug(f"[DeepSeek] 流式请求体: {json.dumps(request_body, ensure_ascii=False)[:500]}")

        chunk_count = 0
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
                logger.info(f"[DeepSeek] 流式响应状态: {response.status_code}")
                
                if not response.is_success:
                    error_text = response.read().decode()
                    logger.error(f"[DeepSeek] 流式请求失败: status={response.status_code}, error={error_text[:500]}")
                    raise LLMServiceError(
                        f"DeepSeek API error: {error_text}",
                        {"status_code": response.status_code, "provider": "deepseek"},
                    )

                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            logger.info(f"[DeepSeek] 流式完成, 共接收{chunk_count}个chunk")
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    chunk_count += 1
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            raise LLMServiceError(
                "DeepSeek API streaming request timed out",
                {"timeout": self._timeout, "provider": "deepseek", "model": model},
            )
        except httpx.RequestError as e:
            raise LLMServiceError(
                f"DeepSeek API streaming request failed: {e}",
                {"error": str(e), "provider": "deepseek"},
            )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "DeepSeekProvider":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

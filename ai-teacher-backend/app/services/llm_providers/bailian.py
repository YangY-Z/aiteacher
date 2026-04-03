"""Alibaba Cloud Bailian (阿里云百炼) LLM Provider implementation using OpenAI-compatible API."""

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


class BailianProvider(BaseLLMProvider):
    """Alibaba Cloud Bailian (阿里云百炼) provider implementation.

    Uses OpenAI-compatible API for communication with Qwen models.
    
    API Documentation: https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api

    Features:
    - OpenAI-compatible interface
    - Supports thinking mode (深度思考) for Qwen models
    - Streaming support with reasoning_content for thinking process
    """

    API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

    def __init__(
        self,
        api_key: str,
        default_model: str = "qwen-plus",
        timeout: float = 60.0,
        max_retries: int = 3,
        enable_thinking: bool = False,
    ) -> None:
        """Initialize Bailian provider.

        Args:
            api_key: Alibaba Cloud Bailian API key (DASHSCOPE_API_KEY).
            default_model: Default model to use (e.g., qwen-plus, qwen-turbo, qwen3.5-35b-a3b).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            enable_thinking: Enable thinking mode for supported models.
        """
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout
        self._max_retries = max_retries
        self._enable_thinking = enable_thinking
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
            Provider name 'bailian'.
        """
        return "bailian"

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
        """Build the request body for Bailian API.

        Args:
            messages: List of chat messages.
            model: Model name.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters (e.g., enable_thinking=True).

        Returns:
            Request body dictionary.
        """
        body: dict[str, Any] = {
            "model": model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Support for thinking mode (深度思考)
        # Can be enabled via kwargs or instance setting
        enable_thinking = kwargs.get("enable_thinking", self._enable_thinking)
        if enable_thinking:
            # For httpx, put directly in body (not extra_body like OpenAI SDK)
            body["enable_thinking"] = True

        # Add any other extra parameters
        for key, value in kwargs.items():
            if key not in ("enable_thinking",) and value is not None:
                body[key] = value

        return body

    def _parse_response(
        self,
        response: httpx.Response,
        model: str,
    ) -> ChatCompletionResponse:
        """Parse the API response.

        Args:
            response: HTTP response from Bailian API.
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
                f"Failed to parse Bailian API response: {e}",
                {"response_text": response.text[:500]},
            )

        if not response.is_success:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            error_code = data.get("error", {}).get("code", "UNKNOWN")
            raise LLMServiceError(
                f"Bailian API error: {error_msg}",
                {
                    "status_code": response.status_code,
                    "error_code": error_code,
                    "provider": "bailian",
                },
            )

        choices = data.get("choices", [])
        if not choices:
            raise LLMServiceError(
                "Empty response from Bailian API",
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
        """Send chat completion request to Bailian API.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters (e.g., enable_thinking=True).

        Returns:
            ChatCompletionResponse with the result.

        Raises:
            LLMServiceError: If the API call fails.
        """
        if not self.is_available():
            raise LLMServiceError(
                "Bailian provider not configured: missing API key",
                {"provider": "bailian"},
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

        logger.info(f"[Bailian] 发送请求: url={url}, model={model}, messages_count={len(messages)}")
        logger.debug(f"[Bailian] 请求体: {json.dumps(request_body, ensure_ascii=False)[:500]}")

        try:
            response = client.post(url, json=request_body)
            logger.info(f"[Bailian] 响应状态: {response.status_code}")
            
            if not response.is_success:
                logger.error(f"[Bailian] 请求失败: {response.text[:500]}")
            
            return self._parse_response(response, model)
        except httpx.TimeoutException:
            logger.error(f"[Bailian] 请求超时: timeout={self._timeout}")
            raise LLMServiceError(
                "Bailian API request timed out",
                {
                    "timeout": self._timeout,
                    "provider": "bailian",
                    "model": model,
                },
            )
        except httpx.RequestError as e:
            logger.error(f"[Bailian] 请求错误: {e}")
            raise LLMServiceError(
                f"Bailian API request failed: {e}",
                {"error": str(e), "provider": "bailian"},
            )

    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chat completion request to Bailian API.

        Supports thinking mode with reasoning_content in streaming chunks.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters (e.g., enable_thinking=True).

        Yields:
            Chunks of content as they arrive.

        Raises:
            LLMServiceError: If the API call fails.
        """
        if not self.is_available():
            raise LLMServiceError(
                "Bailian provider not configured: missing API key",
                {"provider": "bailian"},
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

        logger.info(f"[Bailian] 发送流式请求: url={url}, model={model}")
        logger.debug(f"[Bailian] 流式请求体: {json.dumps(request_body, ensure_ascii=False)[:500]}")

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
                logger.info(f"[Bailian] 流式响应状态: {response.status_code}")
                
                if not response.is_success:
                    error_text = response.read().decode()
                    logger.error(f"[Bailian] 流式请求失败: status={response.status_code}, error={error_text[:500]}")
                    raise LLMServiceError(
                        f"Bailian API error: {error_text}",
                        {"status_code": response.status_code, "provider": "bailian"},
                    )

                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            logger.info(f"[Bailian] 流式完成, 共接收{chunk_count}个chunk")
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                # Standard content
                                content = delta.get("content", "")
                                if content:
                                    chunk_count += 1
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            raise LLMServiceError(
                "Bailian API streaming request timed out",
                {"timeout": self._timeout, "provider": "bailian", "model": model},
            )
        except httpx.RequestError as e:
            raise LLMServiceError(
                f"Bailian API streaming request failed: {e}",
                {"error": str(e), "provider": "bailian"},
            )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "BailianProvider":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

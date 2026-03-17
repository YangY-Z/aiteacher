"""LLM Service for interacting with various LLM providers."""

import json
import logging
from typing import Any, Optional, Generator

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.services.llm_providers import (
    BaseLLMProvider,
    ChatMessage,
    LLMProviderFactory,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM providers.

    This service provides a high-level interface for LLM operations,
    abstracting away the provider-specific details.

    Follows SOLID principles:
    - Single Responsibility: Only LLM operations
    - Dependency Inversion: Depends on BaseLLMProvider abstraction
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialize the LLM service.

        Args:
            provider: LLM provider instance. If None, uses default from config.
        """
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        """Get the LLM provider instance.

        Returns:
            Provider instance.
        """
        if self._provider is None:
            self._provider = LLMProviderFactory.create_provider()
        return self._provider

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat message to the LLM.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message to send.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters (e.g., thinking=True).

        Returns:
            LLM response content.

        Raises:
            LLMServiceError: If the API call fails.
        """
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_message),
        ]

        # Add Zhipu-specific thinking mode if enabled
        if settings.zhipu_enable_thinking and "thinking" not in kwargs:
            kwargs["thinking"] = {"type": "enabled"}

        try:
            response = self.provider.chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            )
            return response.content
        except Exception as e:
            logger.exception(f"LLM chat failed: {e}")
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(
                f"LLM API call failed: {e}",
                {"error": str(e)},
            )

    def chat_with_history(
        self,
        system_prompt: str,
        conversation_history: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat message with conversation history.

        Args:
            system_prompt: System prompt for the conversation.
            conversation_history: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLM response content.

        Raises:
            LLMServiceError: If the API call fails.
        """
        messages = [ChatMessage(role="system", content=system_prompt)]

        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append(ChatMessage(role=role, content=content))

        # Add Zhipu-specific thinking mode if enabled
        if settings.zhipu_enable_thinking and "thinking" not in kwargs:
            kwargs["thinking"] = {"type": "enabled"}

        try:
            response = self.provider.chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            )
            return response.content
        except Exception as e:
            logger.exception(f"LLM chat with history failed: {e}")
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(
                f"LLM API call failed: {e}",
                {"error": str(e)},
            )

    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat message and parse the response as JSON.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message to send.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Parsed JSON response.

        Raises:
            LLMServiceError: If parsing fails.
        """
        response = self.chat(
            system_prompt, user_message, temperature, max_tokens, **kwargs
        )

        try:
            # Try to extract JSON from the response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Return a default structure if parsing fails
            return {
                "response_type": "讲解",
                "content": {"introduction": response[:200] if response else ""},
                "whiteboard": {"formulas": [], "diagrams": []},
                "next_action": "wait_for_student",
                "parse_error": str(e),
            }

    def is_available(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if provider is properly configured.
        """
        return self.provider.is_available()

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream a chat message from the LLM.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message to send.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of content as they arrive.

        Raises:
            LLMServiceError: If the API call fails.
        """
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_message),
        ]

        # Add Zhipu-specific thinking mode if enabled
        if settings.zhipu_enable_thinking and "thinking" not in kwargs:
            kwargs["thinking"] = {"type": "enabled"}

        try:
            yield from self.provider.stream_chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            )
        except Exception as e:
            logger.exception(f"LLM stream chat failed: {e}")
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(
                f"LLM API call failed: {e}",
                {"error": str(e)},
            )


# Global LLM service instance
llm_service = LLMService()
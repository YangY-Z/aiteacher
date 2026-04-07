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

    def _add_thinking_mode(self, kwargs: dict[str, Any]) -> None:
        """Add provider-specific thinking mode to kwargs if enabled.

        Args:
            kwargs: Keyword arguments dict to modify in-place.
        """
        provider = settings.llm_provider.lower()
        
        # Zhipu AI thinking mode
        if provider == "zhipu" and settings.zhipu_enable_thinking:
            if "thinking" not in kwargs:
                kwargs["thinking"] = {"type": "enabled"}
        
        # Alibaba Cloud Bailian thinking mode
        elif provider == "bailian" and settings.bailian_enable_thinking:
            if "enable_thinking" not in kwargs:
                kwargs["enable_thinking"] = True

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        trace_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Send a chat message to the LLM.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message to send.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            trace_id: 链路追踪ID.
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

        # Add provider-specific thinking mode if enabled
        self._add_thinking_mode(kwargs)

        logger.info(f"[{trace_id}] === 调用LLM API ===")
        logger.info(f"[{trace_id}] === 发送给模型 ===")
        logger.info(f"[{trace_id}] System Prompt:\n{system_prompt}")
        logger.info(f"[{trace_id}] User Message:\n{user_message}")

        try:
            response = self.provider.chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            )
            logger.info(f"[{trace_id}] === 模型输出 ===")
            logger.info(f"[{trace_id}] {response.content}")
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
        trace_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Send a chat message with conversation history.

        Args:
            system_prompt: System prompt for the conversation.
            conversation_history: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            trace_id: 链路追踪ID.
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

        # Add provider-specific thinking mode if enabled
        self._add_thinking_mode(kwargs)

        logger.info(f"[{trace_id}] === 调用LLM API (with history) ===")
        logger.info(f"[{trace_id}] === 发送给模型 ===")
        logger.info(f"[{trace_id}] System Prompt:\n{system_prompt}")
        logger.info(f"[{trace_id}] Conversation History ({len(conversation_history)} messages):\n{json.dumps(conversation_history, ensure_ascii=False, indent=2)}")

        try:
            response = self.provider.chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            )
            logger.info(f"[{trace_id}] === 模型输出 ===")
            logger.info(f"[{trace_id}] {response.content}")
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
        history: Optional[list[dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        trace_id: str = "",
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream a chat message from the LLM.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message to send.
            history: Conversation history (list of {"role": "user/assistant", "content": "..."}).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            trace_id: 链路追踪ID.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of content as they arrive.

        Raises:
            LLMServiceError: If the API call fails.
        """
        messages = [ChatMessage(role="system", content=system_prompt)]
        
        # 添加历史对话
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # 标准化角色名称
                if role == "assistant":
                    messages.append(ChatMessage(role="assistant", content=content))
                else:
                    messages.append(ChatMessage(role="user", content=content))
        
        # 添加当前用户消息
        messages.append(ChatMessage(role="user", content=user_message))

        # Add provider-specific thinking mode if enabled
        self._add_thinking_mode(kwargs)

        logger.info(f"[{trace_id}] === 步骤4: 调用LLM流式API ===")
        logger.info(f"[{trace_id}] LLM配置: provider={settings.llm_provider}, model={self.provider.default_model}")
        logger.info(f"[{trace_id}] === 发送给模型 ===")
        logger.info(f"[{trace_id}] System Prompt:\n{system_prompt}")
        if history:
            logger.info(f"[{trace_id}] 对话历史: {len(history)}条消息")
            for i, msg in enumerate(history):
                logger.debug(f"[{trace_id}] 历史[{i}] {msg.get('role')}: {msg.get('content')[:50]}...")
        logger.info(f"[{trace_id}] User Message:\n{user_message}")
        logger.debug(f"[{trace_id}] 用户消息长度: {len(user_message)}字符")

        chunk_count = 0
        full_response = ""  # 收集完整响应
        try:
            for chunk in self.provider.stream_chat_completion(
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                **kwargs,
            ):
                chunk_count += 1
                full_response += chunk
                yield chunk
            
            logger.info(f"[{trace_id}] === 步骤5: LLM流式响应完成, 共{chunk_count}个chunk ===")
            logger.info(f"[{trace_id}] === 模型输出 ===")
            logger.info(f"[{trace_id}] {full_response}")
        except Exception as e:
            logger.error(f"[{trace_id}] LLM流式调用失败: {e}")
            logger.exception(f"[{trace_id}] 详细错误信息")
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(
                f"LLM API call failed: {e}",
                {"error": str(e)},
            )


# Global LLM service instance
llm_service = LLMService()
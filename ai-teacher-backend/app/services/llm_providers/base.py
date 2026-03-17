"""Base LLM Provider interface using Protocol for dependency injection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union, Generator


class MessageRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """Chat message structure."""

    role: Union[MessageRole, str]
    content: str

    def __post_init__(self) -> None:
        """Normalize role to MessageRole enum if string is provided."""
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for API request."""
        role_value = self.role.value if isinstance(self.role, MessageRole) else self.role
        return {"role": role_value, "content": self.content}


@dataclass
class ChatCompletionResponse:
    """Standardized chat completion response."""

    content: str
    model: str
    usage: Optional[dict[str, int]] = None
    finish_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], model: str) -> "ChatCompletionResponse":
        """Create response from dictionary.

        Args:
            data: Response data from LLM API.
            model: Model name used for the request.

        Returns:
            ChatCompletionResponse instance.
        """
        return cls(
            content=data.get("content", ""),
            model=model,
            usage=data.get("usage"),
            finish_reason=data.get("finish_reason"),
        )


@dataclass
class ChatCompletionRequest:
    """Standardized chat completion request."""

    messages: list[ChatMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    extra_params: Optional[dict[str, Any]] = None

    def to_messages_dict(self) -> list[dict[str, str]]:
        """Convert messages to list of dictionaries."""
        return [msg.to_dict() for msg in self.messages]


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    Follows SOLID principles:
    - Interface Segregation: Only essential methods exposed
    - Dependency Inversion: High-level modules depend on this abstraction
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name string (e.g., 'zhipu', 'openai').
        """
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Get the default model for this provider.

        Returns:
            Default model name.
        """
        pass

    @abstractmethod
    def chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """Send chat completion request.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ChatCompletionResponse with the result.

        Raises:
            LLMServiceError: If the API call fails.
        """
        pass

    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chat completion request.

        Args:
            messages: List of chat messages.
            model: Model to use, defaults to provider's default model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of content as they arrive.

        Raises:
            LLMServiceError: If the API call fails.
        """
        # Default implementation: fall back to non-streaming
        response = self.chat_completion(messages, model, temperature, max_tokens, **kwargs)
        yield response.content

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available.

        Returns:
            True if provider can make API calls, False otherwise.
        """
        pass

    def create_system_message(self, content: str) -> ChatMessage:
        """Create a system message.

        Args:
            content: Message content.

        Returns:
            ChatMessage with system role.
        """
        return ChatMessage(role=MessageRole.SYSTEM, content=content)

    def create_user_message(self, content: str) -> ChatMessage:
        """Create a user message.

        Args:
            content: Message content.

        Returns:
            ChatMessage with user role.
        """
        return ChatMessage(role=MessageRole.USER, content=content)

    def create_assistant_message(self, content: str) -> ChatMessage:
        """Create an assistant message.

        Args:
            content: Message content.

        Returns:
            ChatMessage with assistant role.
        """
        return ChatMessage(role=MessageRole.ASSISTANT, content=content)

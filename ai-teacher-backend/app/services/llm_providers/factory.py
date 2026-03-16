"""LLM Provider Factory for creating provider instances."""

import logging
from enum import Enum
from typing import Optional

from app.core.config import settings
from app.services.llm_providers.base import BaseLLMProvider
from app.services.llm_providers.zhipu import ZhipuProvider

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""

    ZHIPU = "zhipu"
    # Future providers can be added here:
    # OPENAI = "openai"
    # ANTHROPIC = "anthropic"
    # DEEPSEEK = "deepseek"


class LLMProviderFactory:
    """Factory for creating LLM provider instances.

    Follows the Factory Pattern and Dependency Inversion Principle.
    New providers can be added by:
    1. Creating a new provider class inheriting from BaseLLMProvider
    2. Adding the provider type to LLMProviderType enum
    3. Adding the creation logic in create_provider method
    """

    _providers: dict[str, BaseLLMProvider] = {}

    @classmethod
    def create_provider(
        cls,
        provider_type: Optional[LLMProviderType] = None,
        use_cache: bool = False,
        **kwargs,
    ) -> BaseLLMProvider:
        """Create or return cached provider instance.

        Args:
            provider_type: Type of provider to create. If None, uses default from config.
            use_cache: Whether to use cached provider. Default False to avoid stale config.
            **kwargs: Additional arguments for provider initialization.

        Returns:
            Provider instance.

        Raises:
            ValueError: If provider type is not supported.
        """
        if provider_type is None:
            provider_type = LLMProviderType(settings.llm_provider)

        # Only use cache if explicitly requested
        cache_key = provider_type.value
        if use_cache and cache_key in cls._providers and not kwargs:
            return cls._providers[cache_key]

        provider = cls._create_provider_instance(provider_type, **kwargs)

        # Only cache if explicitly requested
        if use_cache and not kwargs:
            cls._providers[cache_key] = provider

        return provider

    @classmethod
    def _create_provider_instance(
        cls,
        provider_type: LLMProviderType,
        **kwargs,
    ) -> BaseLLMProvider:
        """Create a new provider instance.

        Args:
            provider_type: Type of provider to create.
            **kwargs: Additional arguments for provider initialization.

        Returns:
            New provider instance.

        Raises:
            ValueError: If provider type is not supported.
        """
        # Force reload settings to get fresh config (fixes uvicorn reload issue)
        from app.core.config import get_settings
        fresh_settings = get_settings()

        if provider_type == LLMProviderType.ZHIPU:
            return ZhipuProvider(
                api_key=kwargs.get("api_key", fresh_settings.zhipu_api_key),
                default_model=kwargs.get("default_model", fresh_settings.zhipu_model),
                timeout=kwargs.get("timeout", fresh_settings.llm_timeout),
            )

        # Future providers can be added here:
        # elif provider_type == LLMProviderType.OPENAI:
        #     return OpenAIProvider(...)

        raise ValueError(f"Unsupported LLM provider type: {provider_type}")

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider types.

        Returns:
            List of provider type names.
        """
        return [p.value for p in LLMProviderType]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the provider cache."""
        for provider in cls._providers.values():
            if hasattr(provider, "close"):
                provider.close()
        cls._providers.clear()


def get_llm_provider(provider_type: Optional[LLMProviderType] = None) -> BaseLLMProvider:
    """Convenience function to get LLM provider.

    Args:
        provider_type: Type of provider. If None, uses default from config.

    Returns:
        Provider instance.
    """
    return LLMProviderFactory.create_provider(provider_type)

"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (where .env file is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI Virtual Teacher"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    # Data directory for loading JSON files
    data_dir: str = "/Users/zhaoyang/iFlow/aiteacher"

    # API
    api_prefix: str = "/api/v1"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # LLM Configuration
    llm_provider: str = "zhipu"
    llm_timeout: float = 60.0
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048

    # Zhipu AI Configuration
    zhipu_api_key: Optional[str] = None
    zhipu_model: str = "glm-4"

    # GLM-5 specific: enable thinking mode
    zhipu_enable_thinking: bool = False

    # Alibaba Cloud Bailian (阿里云百炼) Configuration
    bailian_api_key: Optional[str] = None  # DASHSCOPE_API_KEY
    bailian_model: str = "qwen-plus"  # qwen-plus, qwen-turbo, qwen3.5-35b-a3b
    bailian_enable_thinking: bool = False  # Enable thinking mode for supported models

    # CORS - allow all origins in development
    cors_origins: list[str] = ["*"]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

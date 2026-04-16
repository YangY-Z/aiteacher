"""Protocols for tool interfaces.

This module exports all protocol interfaces for tool dependencies.
"""

from app.services.tools.protocols.ai_image_generator import AIImageGeneratorProtocol
from app.services.tools.protocols.animation_generator import AnimationGeneratorProtocol
from app.services.tools.protocols.image_repository import ImageRepositoryProtocol
from app.services.tools.protocols.usage_log_repository import UsageLogRepositoryProtocol

__all__ = [
    "ImageRepositoryProtocol",
    "AnimationGeneratorProtocol",
    "AIImageGeneratorProtocol",
    "UsageLogRepositoryProtocol",
]

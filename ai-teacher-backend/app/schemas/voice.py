"""Schemas for voice input and output capabilities."""

from typing import Optional

from pydantic import BaseModel, Field


class VoiceCapabilities(BaseModel):
    """Voice capability flags exposed to the frontend."""

    stt_provider: str = "browser"
    tts_provider: str = "edge"
    supports_browser_stt: bool = True
    supports_browser_tts: bool = True
    supports_cloud_stt: bool = False
    supports_cloud_tts: bool = True
    max_recording_seconds: int = 30
    max_tts_chars: int = 220
    default_voice: str = "zh-CN-XiaoxiaoNeural"


class VoiceSynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""

    text: str = Field(..., min_length=1, max_length=2000)
    voice: str = "zh-CN-default"
    speed: float = Field(1.0, ge=0.5, le=2.0)


class VoiceSynthesisResponse(BaseModel):
    """Response for text-to-speech synthesis."""

    provider: str
    audio_id: str
    audio_url: Optional[str] = None
    cache_hit: bool = False
    should_use_browser_tts: bool = True


class VoiceTranscriptionRequest(BaseModel):
    """Request for cloud speech-to-text transcription."""

    audio_base64: str = Field(..., min_length=1)
    mime_type: str = "audio/webm"
    language: str = "zh-CN"


class VoiceTranscriptionResponse(BaseModel):
    """Response for cloud speech-to-text transcription."""

    provider: str
    text: str
    confidence: Optional[float] = None

"""Voice input/output API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.voice import (
    VoiceCapabilities,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse,
    VoiceTranscriptionRequest,
    VoiceTranscriptionResponse,
)
from app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/capabilities", response_model=VoiceCapabilities)
async def get_voice_capabilities() -> VoiceCapabilities:
    """Return the active voice strategy and limits."""
    return voice_service.get_capabilities()


@router.post("/synthesize", response_model=VoiceSynthesisResponse)
async def synthesize_voice(request: VoiceSynthesisRequest) -> VoiceSynthesisResponse:
    """Prepare speech synthesis.

    EdgeTTS is used when configured and available; browser TTS remains fallback.
    """
    return await voice_service.synthesize(request)


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    request: VoiceTranscriptionRequest,
) -> VoiceTranscriptionResponse:
    """Transcribe audio through a cloud provider when configured."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cloud STT is not configured. Use browser speech recognition by default.",
    )

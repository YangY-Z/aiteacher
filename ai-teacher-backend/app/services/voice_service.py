"""Low-cost voice service facade.

The current default keeps speech recognition and synthesis in the browser to
avoid server-side usage cost. Cloud providers can be added behind this facade.
"""

import hashlib
import importlib.util
import logging
from pathlib import Path

from app.core.config import settings
from app.schemas.voice import (
    VoiceCapabilities,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse,
)

logger = logging.getLogger(__name__)


class VoiceService:
    """Voice capability and cache-key service."""

    def get_capabilities(self) -> VoiceCapabilities:
        """Return the current voice feature mode."""
        edge_available = importlib.util.find_spec("edge_tts") is not None
        provider = settings.voice_tts_provider.lower()
        use_edge = provider == "edge" and edge_available
        return VoiceCapabilities(
            tts_provider="edge" if use_edge else "browser",
            supports_cloud_tts=use_edge,
            default_voice=settings.voice_tts_voice,
        )

    async def synthesize(
        self,
        request: VoiceSynthesisRequest,
    ) -> VoiceSynthesisResponse:
        """Generate or prepare speech synthesis with cache-first behavior."""
        provider = settings.voice_tts_provider.lower()
        voice = request.voice if request.voice != "zh-CN-default" else settings.voice_tts_voice
        cache_source = f"{provider}|{voice}|{request.speed}|{request.text.strip()}"
        audio_id = hashlib.sha256(cache_source.encode("utf-8")).hexdigest()[:24]

        if provider == "edge":
            edge_response = await self._synthesize_with_edge(request, voice, audio_id)
            if edge_response:
                return edge_response

        return VoiceSynthesisResponse(
            provider="browser",
            audio_id=audio_id,
            audio_url=None,
            cache_hit=False,
            should_use_browser_tts=True,
        )

    async def _synthesize_with_edge(
        self,
        request: VoiceSynthesisRequest,
        voice: str,
        audio_id: str,
    ) -> VoiceSynthesisResponse | None:
        """Generate speech with EdgeTTS when available."""
        if importlib.util.find_spec("edge_tts") is None:
            logger.warning("edge-tts is not installed; falling back to browser TTS")
            return None

        import edge_tts

        audio_dir = Path(settings.voice_audio_dir)
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{audio_id}.mp3"
        audio_url = f"/media/voice/{audio_id}.mp3"

        if audio_path.exists() and audio_path.stat().st_size > 0:
            return VoiceSynthesisResponse(
                provider="edge",
                audio_id=audio_id,
                audio_url=audio_url,
                cache_hit=True,
                should_use_browser_tts=False,
            )

        rate = self._speed_to_edge_rate(request.speed)
        try:
            communicate = edge_tts.Communicate(request.text.strip(), voice=voice, rate=rate)
            await communicate.save(str(audio_path))
        except Exception as exc:
            logger.warning("EdgeTTS synthesis failed; falling back to browser TTS: %s", exc)
            if audio_path.exists():
                audio_path.unlink(missing_ok=True)
            return None

        return VoiceSynthesisResponse(
            provider="edge",
            audio_id=audio_id,
            audio_url=audio_url,
            cache_hit=False,
            should_use_browser_tts=False,
        )

    @staticmethod
    def _speed_to_edge_rate(speed: float) -> str:
        """Convert a 1.0-based speed to EdgeTTS rate syntax."""
        percent = int(round((speed - 1.0) * 100))
        percent = max(-50, min(100, percent))
        sign = "+" if percent >= 0 else ""
        return f"{sign}{percent}%"


voice_service = VoiceService()

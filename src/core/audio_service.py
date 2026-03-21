"""Silero TTS audio service for Russian pronunciation."""
import hashlib
import asyncio
from pathlib import Path
from typing import Optional
import logging

from src.config import AUDIO_CACHE_DIR

logger = logging.getLogger(__name__)

# Silero TTS model repository
SILERO_REPO = "snakers4/silero-api"
SILERO_MODEL = "silero_v5"
SILERO_SPEAKER = "aidar"


class AudioService:
    _model = None
    _device = None
    _initialized = False

    @classmethod
    async def initialize(cls) -> bool:
        """Initialize Silero TTS model."""
        if cls._initialized:
            return True

        try:
            import torch
            import torchaudio

            if torch.cuda.is_available():
                cls._device = "cuda"
            else:
                cls._device = "cpu"

            # Download model on first use
            torch.hub.set_dir(str(Path(__file__).parent.parent.parent / "data" / "cache"))
            cls._model = torch.hub.load(
                SILERO_REPO, model=SILERO_MODEL, trust_repo=True
            )
            cls._model.to(cls._device)
            cls._initialized = True
            logger.info(f"Silero TTS initialized on {cls._device}")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize Silero TTS: {e}")
            return False

    @classmethod
    def get_cache_path(cls, text: str) -> Path:
        """Get cached audio file path for text."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return AUDIO_CACHE_DIR / f"{text_hash}.wav"

    @classmethod
    async def generate_audio(cls, text: str) -> Optional[Path]:
        """Generate TTS audio for text. Returns cached path if available."""
        cache_path = cls.get_cache_path(text)
        if cache_path.exists():
            return cache_path

        if not cls._initialized:
            success = await cls.initialize()
            if not success:
                return None

        try:
            import torch
            import torchaudio

            # Clean text for TTS (remove stress marks for cleaner output)
            clean_text = text.replace("\u0301", "")

            audio = cls._model.apply_tts(
                text=clean_text,
                speaker=SILERO_SPEAKER,
                sample_rate=48000,
            )

            # Save to cache
            torchaudio.save(str(cache_path), audio.unsqueeze(1), 48000)
            logger.debug(f"Generated audio for: {text[:30]}")
            return cache_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    @classmethod
    async def preload_batch(cls, texts: list[str]) -> None:
        """Preload audio for a batch of texts."""
        for text in texts:
            path = cls.get_cache_path(text)
            if not path.exists():
                asyncio.create_task(cls.generate_audio(text))

    @classmethod
    def clear_cache(cls) -> int:
        """Clear audio cache. Returns number of files removed."""
        count = 0
        for f in AUDIO_CACHE_DIR.glob("*.wav"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count

    @classmethod
    def get_cache_size_mb(cls) -> float:
        """Get total cache size in MB."""
        total = 0
        for f in AUDIO_CACHE_DIR.glob("*.wav"):
            try:
                total += f.stat().st_size
            except OSError:
                pass
        return total / (1024 * 1024)

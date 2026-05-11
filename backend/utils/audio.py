"""
Audio preprocessing utilities for Whisper transcription.
Handles format conversion, duration validation, and sample rate normalization.
"""
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Supported input formats
SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm", ".mp4"}
MAX_AUDIO_DURATION_SECONDS = 300  # 5 minutes
MAX_AUDIO_SIZE_MB = 25


def validate_audio_file(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate an audio file for Whisper processing.
    Returns (is_valid, error_message).
    """
    if not file_path.exists():
        return False, "File does not exist"

    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_FORMATS:
        return False, f"Unsupported format '{suffix}'. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"

    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        return False, f"File too large ({size_mb:.1f}MB). Maximum: {MAX_AUDIO_SIZE_MB}MB"

    return True, None


def convert_to_wav(input_path: Path, target_sr: int = 16000) -> Path:
    """
    Convert audio to 16kHz mono WAV (Whisper's preferred input format).
    Returns path to the converted file (in temp directory).
    """
    output_path = Path(settings.TEMP_DIR) / f"audio_{os.urandom(8).hex()}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-ar", str(target_sr),   # Sample rate
            "-ac", "1",               # Mono
            "-c:a", "pcm_s16le",      # 16-bit PCM
            "-y",                     # Overwrite
            str(output_path)
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg conversion failed: {result.stderr}")
            raise RuntimeError(f"Audio conversion failed: {result.stderr[:200]}")

        return output_path

    except FileNotFoundError:
        logger.warning("ffmpeg not found — returning original file (Whisper may still handle it)")
        return input_path
    except subprocess.TimeoutExpired:
        raise RuntimeError("Audio conversion timed out")


def get_audio_duration(file_path: Path) -> Optional[float]:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-i", str(file_path),
                "-show_entries", "format=duration",
                "-v", "quiet", "-of", "csv=p=0"
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def cleanup_audio_temp(file_path: Path):
    """Remove temporary audio file if it's in the temp directory."""
    try:
        if str(settings.TEMP_DIR) in str(file_path) and file_path.exists():
            file_path.unlink()
    except OSError:
        pass

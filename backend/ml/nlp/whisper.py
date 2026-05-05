import subprocess
import json
import numpy as np
from pathlib import Path
from backend.core.exceptions import InvalidFileError, ValidationError, InferenceError

class WhisperTranscriber:
    SUPPORTED_INPUT_FORMATS = {".wav", ".mp3", ".webm", ".ogg", ".m4a"}
    MAX_DURATION_SECONDS = 60
    
    @staticmethod
    def transcribe(audio_file_path: Path, model, language: str = "en") -> dict:
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise InvalidFileError(f"Audio file not found: {audio_path}")
            
        wav_path = None
        try:
            if audio_path.suffix.lower() != ".wav":
                wav_path = audio_path.with_suffix(".converted.wav")
                WhisperTranscriber._convert_to_wav(audio_path, wav_path)
                process_path = wav_path
            else:
                process_path = audio_path
                
            duration = WhisperTranscriber._get_duration(process_path)
            if duration > WhisperTranscriber.MAX_DURATION_SECONDS:
                raise ValidationError(f"Audio too long ({duration:.0f}s). Max {WhisperTranscriber.MAX_DURATION_SECONDS}s.")
                
            result = model.transcribe(
                str(process_path), language=language, verbose=False,
                word_timestamps=True, fp16=False, condition_on_previous_text=False,
                no_speech_threshold=0.6, logprob_threshold=-1.0
            )
            
            avg_logprob = np.mean([s["avg_logprob"] for s in result["segments"]]) if result["segments"] else -1
            confidence = float(min(1.0, max(0.0, np.exp(avg_logprob))))
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "confidence": round(confidence, 3),
                "duration_seconds": round(duration, 1),
                "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in result["segments"]]
            }
        finally:
            if wav_path and wav_path.exists():
                wav_path.unlink()

    @staticmethod
    def _convert_to_wav(input_path: Path, output_path: Path):
        cmd = [
            "ffmpeg", "-i", str(input_path), "-acodec", "pcm_s16le", 
            "-ac", "1", "-ar", "16000", "-y", str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise InferenceError(f"Audio conversion failed: {result.stderr[:200]}")

    @staticmethod
    def _get_duration(wav_path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(wav_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return 0.0
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))

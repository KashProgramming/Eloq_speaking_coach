import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from faster_whisper import WhisperModel
from pydub import AudioSegment

from app.core.config import get_settings
from app.services.storage_service import upload_audio

ALLOWED_EXTENSIONS = {"wav", "webm", "mp3"}
ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/x-wav", "audio/webm", "audio/mpeg", "audio/mp3"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_DURATION = 30
MAX_DURATION = 180


@dataclass
class ProcessedAudio:
    audio_url: str
    transcript: str
    duration: float
    segments: list[dict]


@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModel:
    settings = get_settings()
    return WhisperModel(
        settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


def _validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format")
    return ext


def _validate_content_type(content_type: str | None) -> None:
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format")


async def process_audio_upload(audio_file: UploadFile, enforce_duration_bounds: bool = True) -> ProcessedAudio:
    _validate_extension(audio_file.filename or "")
    _validate_content_type(audio_file.content_type)

    raw_bytes = await audio_file.read()
    if len(raw_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    source_fd, source_path = tempfile.mkstemp(suffix=Path(audio_file.filename or "audio.webm").suffix or ".webm")
    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(source_fd)
    os.close(wav_fd)

    try:
        with open(source_path, "wb") as file_obj:
            file_obj.write(raw_bytes)

        audio = AudioSegment.from_file(source_path)
        source_duration = len(audio) / 1000.0
        if enforce_duration_bounds and not (MIN_DURATION <= source_duration <= MAX_DURATION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio must be {MIN_DURATION}-{MAX_DURATION} seconds",
            )

        audio_url = upload_audio(source_path)

        audio.export(wav_path, format="wav")
        model = get_whisper_model()
        segments, info = model.transcribe(wav_path, language="en")

        collected_segments = []
        transcript_parts: list[str] = []
        for seg in segments:
            text = (seg.text or "").strip()
            if text:
                transcript_parts.append(text)
            collected_segments.append({"start": float(seg.start), "end": float(seg.end), "text": text})

        transcript = " ".join(transcript_parts).strip()
        duration = float(info.duration or source_duration)

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio quality too low for transcription",
            )

        return ProcessedAudio(
            audio_url=audio_url,
            transcript=transcript,
            duration=round(duration, 1),
            segments=collected_segments,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio quality too low for transcription",
        ) from exc
    finally:
        for path in (source_path, wav_path):
            if path and os.path.exists(path):
                os.remove(path)

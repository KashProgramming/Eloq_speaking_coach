import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, status
from groq import Groq

from app.core.config import get_settings
from app.services.storage_service import upload_audio

# Cache the Groq client
_groq_tts_client = None


def get_groq_tts_client() -> Groq:
    """Get or create the Groq TTS client."""
    global _groq_tts_client
    if _groq_tts_client is None:
        settings = get_settings()
        if not settings.groq_tts_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TTS service not configured. Please set GROQ_TTS_API_KEY in environment."
            )
        # Initialize Groq client with TTS-specific API key
        _groq_tts_client = Groq(api_key=settings.groq_tts_api_key)
    return _groq_tts_client


def generate_speech(text: str) -> str:
    """
    Generate speech from text using Groq TTS API and upload to Cloudinary.
    
    Args:
        text: The text to convert to speech
        
    Returns:
        str: The Cloudinary URL of the generated audio
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    
    # Create temporary file for the audio
    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)
    
    try:
        settings = get_settings()
        client = get_groq_tts_client()
        
        # Generate speech using Groq API
        response = client.audio.speech.create(
            model=settings.groq_tts_model,
            voice=settings.groq_tts_voice,
            response_format="wav",
            input=text
        )
        
        # Write the audio response to file
        speech_file_path = Path(wav_path)
        response.write_to_file(speech_file_path)
        
        # Upload to Cloudinary
        audio_url = upload_audio(wav_path)
        
        return audio_url
        
    except HTTPException:
        raise
    except Exception as exc:
        # Log the full error for debugging
        print(f"TTS generation error: {type(exc).__name__}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(exc)}"
        ) from exc
    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

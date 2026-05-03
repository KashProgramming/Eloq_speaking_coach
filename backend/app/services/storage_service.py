import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status
from typing import Optional
import re

from app.core.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


def upload_audio(file_path: str) -> str:
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",
            folder=settings.cloudinary_audio_folder,
        )
    except Exception as exc:  # pragma: no cover - external service
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary upload failed",
        ) from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary upload failed",
        )
    return secure_url


def extract_public_id_from_url(url: str) -> Optional[str]:
    """
    Extract Cloudinary public_id from a secure URL.
    Example: https://res.cloudinary.com/cloud/video/upload/v123/folder/file.mp3
    Returns: folder/file
    """
    if not url:
        return None
    
    try:
        # Pattern to match Cloudinary URLs
        # Matches: /upload/v{version}/{public_id}.{extension}
        pattern = r'/upload/(?:v\d+/)?(.+)\.\w+$'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def delete_audio(audio_url: str) -> bool:
    """
    Delete an audio file from Cloudinary.
    Returns True if successful, False otherwise.
    """
    if not audio_url:
        return False
    
    public_id = extract_public_id_from_url(audio_url)
    if not public_id:
        return False
    
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="video",
            invalidate=True
        )
        # Cloudinary returns {'result': 'ok'} on success
        return result.get("result") == "ok"
    except Exception:
        # Log error but don't raise - we want to continue deleting other files
        return False


def delete_multiple_audios(audio_urls: list[str]) -> dict[str, int]:
    """
    Delete multiple audio files from Cloudinary.
    Returns a dict with counts of successful and failed deletions.
    """
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for url in audio_urls:
        if not url:
            results["skipped"] += 1
            continue
            
        if delete_audio(url):
            results["success"] += 1
        else:
            results["failed"] += 1
    
    return results

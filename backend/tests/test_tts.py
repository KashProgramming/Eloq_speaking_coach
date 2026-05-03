"""
Test script for TTS functionality.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tts_service import generate_speech


def test_tts():
    """Test TTS generation with a sample text."""
    print("=" * 60)
    print("Testing TTS Service")
    print("=" * 60)
    
    test_text = "This is a test of the Groq text-to-speech system."
    print(f"\nGenerating speech for: '{test_text}'")
    print("\nThis will:")
    print("1. Use Groq API to generate speech")
    print("2. Generate audio from text")
    print("3. Upload to Cloudinary")
    print("4. Return the audio URL")
    
    try:
        print("\nGenerating...")
        audio_url = generate_speech(test_text)
        print(f"\n✓ Success!")
        print(f"\nAudio URL: {audio_url}")
        print("\nYou can test the audio by opening this URL in your browser.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify GROQ_TTS_API_KEY is set in .env")
        print("2. Verify Cloudinary credentials in .env")
        print("3. Ensure groq is installed: pip install groq")
        raise
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_tts()

"""
Add roleplay_assistant_audio table for storing TTS audio of assistant responses.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()


def add_roleplay_assistant_audio_table():
    """Create roleplay_assistant_audio table."""
    db = SessionLocal()
    try:
        # Check if table exists
        result = db.execute(
            text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='roleplay_assistant_audio'
                """
            )
        )
        exists = result.fetchone() is not None

        if not exists:
            print("Creating roleplay_assistant_audio table...")
            db.execute(
                text(
                    """
                    CREATE TABLE roleplay_assistant_audio (
                        id VARCHAR PRIMARY KEY,
                        session_id VARCHAR NOT NULL,
                        turn_number INTEGER NOT NULL,
                        audio_url VARCHAR NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES roleplay_sessions(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            
            # Create index for faster lookups
            db.execute(
                text(
                    """
                    CREATE INDEX idx_roleplay_assistant_audio_session 
                    ON roleplay_assistant_audio(session_id, turn_number)
                    """
                )
            )
            
            db.commit()
            print("✓ Table created successfully")
        else:
            print("✓ Table already exists")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_roleplay_assistant_audio_table()

"""
Comprehensive migration script for TTS features.
Adds ideal_answer_audio_url to sessions and roleplay_assistant_audio table.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()


def migrate_tts_features():
    """Run all TTS-related migrations."""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("TTS Features Migration")
        print("=" * 60)
        
        # 1. Add ideal_answer_audio_url column to sessions table
        print("\n1. Checking sessions table...")
        result = db.execute(
            text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='sessions' AND column_name='ideal_answer_audio_url'
                """
            )
        )
        exists = result.fetchone() is not None

        if not exists:
            print("   Adding ideal_answer_audio_url column...")
            db.execute(
                text(
                    """
                    ALTER TABLE sessions 
                    ADD COLUMN ideal_answer_audio_url VARCHAR NULL
                    """
                )
            )
            db.commit()
            print("   ✓ Column added successfully")
        else:
            print("   ✓ Column already exists")

        # 2. Create roleplay_assistant_audio table
        print("\n2. Checking roleplay_assistant_audio table...")
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
            print("   Creating roleplay_assistant_audio table...")
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
            print("   ✓ Table created successfully")
        else:
            print("   ✓ Table already exists")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_tts_features()

"""
Add ideal_answer_audio_url column to sessions table.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()


def add_ideal_answer_audio_column():
    """Add ideal_answer_audio_url column to sessions table."""
    db = SessionLocal()
    try:
        # Check if column exists
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
            print("Adding ideal_answer_audio_url column to sessions table...")
            db.execute(
                text(
                    """
                    ALTER TABLE sessions 
                    ADD COLUMN ideal_answer_audio_url VARCHAR NULL
                    """
                )
            )
            db.commit()
            print("✓ Column added successfully")
        else:
            print("✓ Column already exists")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_ideal_answer_audio_column()

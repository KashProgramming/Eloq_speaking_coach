"""
Add roleplay_turn_audio table to store audio URLs for each user turn in roleplay sessions.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.db.session import engine


def add_roleplay_turn_audio_table():
    """Create roleplay_turn_audio table."""
    with engine.begin() as conn:
        # Check if table exists
        result = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'roleplay_turn_audio'
                );
                """
            )
        )
        table_exists = result.scalar()

        if table_exists:
            print("✓ roleplay_turn_audio table already exists")
            return

        # Create the table
        conn.execute(
            text(
                """
                CREATE TABLE roleplay_turn_audio (
                    id VARCHAR PRIMARY KEY,
                    session_id VARCHAR NOT NULL,
                    turn_number INTEGER NOT NULL,
                    audio_url VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES roleplay_sessions(id) ON DELETE CASCADE,
                    UNIQUE (session_id, turn_number)
                );
                """
            )
        )
        print("✓ Created roleplay_turn_audio table")

        # Create index for faster lookups
        conn.execute(
            text(
                """
                CREATE INDEX idx_roleplay_turn_audio_session 
                ON roleplay_turn_audio(session_id);
                """
            )
        )
        print("✓ Created index on roleplay_turn_audio.session_id")


if __name__ == "__main__":
    print("Adding roleplay_turn_audio table...")
    add_roleplay_turn_audio_table()
    print("✓ Migration complete!")

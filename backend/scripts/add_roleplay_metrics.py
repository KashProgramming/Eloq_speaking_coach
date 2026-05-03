"""
Migration script to add comprehensive metrics to roleplay sessions.
Adds fluency, vocabulary, grammar, structure scores and per-turn metrics.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal


def migrate():
    settings = get_settings()
    db = SessionLocal()
    
    try:
        print("Adding comprehensive metrics columns to roleplay_sessions...")
        
        # Add score columns to roleplay_sessions
        db.execute(text("""
            ALTER TABLE roleplay_sessions
            ADD COLUMN IF NOT EXISTS fluency_score INTEGER,
            ADD COLUMN IF NOT EXISTS vocabulary_score INTEGER,
            ADD COLUMN IF NOT EXISTS grammar_score INTEGER,
            ADD COLUMN IF NOT EXISTS structure_score INTEGER
        """))
        
        print("Creating roleplay_turn_metrics table...")
        
        # Create table for per-turn metrics
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS roleplay_turn_metrics (
                id VARCHAR PRIMARY KEY,
                session_id VARCHAR NOT NULL REFERENCES roleplay_sessions(id) ON DELETE CASCADE,
                turn_number INTEGER NOT NULL,
                transcript TEXT NOT NULL,
                duration FLOAT NOT NULL,
                wpm FLOAT NOT NULL,
                fillers INTEGER NOT NULL,
                pauses INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                fluency_score INTEGER NOT NULL,
                vocabulary_score INTEGER NOT NULL,
                grammar_score INTEGER NOT NULL,
                structure_score INTEGER NOT NULL,
                strengths TEXT,
                weaknesses TEXT,
                created_at TIMESTAMP NOT NULL,
                UNIQUE(session_id, turn_number)
            )
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_roleplay_turn_metrics_session_id 
            ON roleplay_turn_metrics(session_id)
        """))
        
        db.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

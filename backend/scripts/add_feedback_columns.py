"""
Add feedback and grammar_mistakes columns to sessions table.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.db.session import engine


def add_feedback_columns():
    """Add feedback and grammar_mistakes columns to sessions table."""
    with engine.begin() as conn:
        # Check if columns exist
        result = conn.execute(
            text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sessions' 
                AND column_name IN ('feedback', 'grammar_mistakes');
                """
            )
        )
        existing_columns = {row[0] for row in result}

        if "feedback" not in existing_columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE sessions 
                    ADD COLUMN feedback TEXT;
                    """
                )
            )
            print("✓ Added feedback column to sessions table")
        else:
            print("✓ feedback column already exists")

        if "grammar_mistakes" not in existing_columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE sessions 
                    ADD COLUMN grammar_mistakes TEXT;
                    """
                )
            )
            print("✓ Added grammar_mistakes column to sessions table")
        else:
            print("✓ grammar_mistakes column already exists")


if __name__ == "__main__":
    print("Adding feedback columns to sessions table...")
    add_feedback_columns()
    print("✓ Migration complete!")

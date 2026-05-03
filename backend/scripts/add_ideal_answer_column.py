"""
Migration script to add ideal_answer column to sessions table if it doesn't exist.
Run this script once to update the database schema.

Usage:
    python -m scripts.add_ideal_answer_column
"""

from sqlalchemy import text
from app.db.session import engine


def add_ideal_answer_column():
    """Add ideal_answer column to sessions table if it doesn't exist."""
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='sessions' AND column_name='ideal_answer'
        """))
        
        column_exists = result.fetchone() is not None
        
        if column_exists:
            print("✓ Column 'ideal_answer' already exists in 'sessions' table")
            return
        
        # Add the column
        print("Adding 'ideal_answer' column to 'sessions' table...")
        conn.execute(text("""
            ALTER TABLE sessions 
            ADD COLUMN ideal_answer TEXT NULL
        """))
        conn.commit()
        print("✓ Successfully added 'ideal_answer' column to 'sessions' table")


if __name__ == "__main__":
    try:
        add_ideal_answer_column()
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

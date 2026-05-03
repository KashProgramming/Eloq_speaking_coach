"""
Migration script to add last_prompt_date column to users table.
Run this once to update the database schema.
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text

from app.db.session import SessionLocal, engine


def migrate():
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='last_prompt_date'
        """))
        
        if result.fetchone():
            print("Column 'last_prompt_date' already exists. No migration needed.")
            return
        
        # Add the column
        db.execute(text("ALTER TABLE users ADD COLUMN last_prompt_date TIMESTAMP NULL"))
        db.commit()
        print("Successfully added 'last_prompt_date' column to users table.")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

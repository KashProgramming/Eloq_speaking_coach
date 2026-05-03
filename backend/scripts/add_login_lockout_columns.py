"""
Migration script to add failed_login_attempts and locked_until columns to users table.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import SessionLocal


def add_login_lockout_columns():
    """Add failed_login_attempts and locked_until columns to users table."""
    db = SessionLocal()
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' 
            AND column_name IN ('failed_login_attempts', 'locked_until')
        """))
        existing_columns = {row[0] for row in result}
        
        # Add failed_login_attempts column if it doesn't exist
        if 'failed_login_attempts' not in existing_columns:
            print("Adding failed_login_attempts column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
            """))
            db.commit()
            print("✓ Added failed_login_attempts column")
        else:
            print("✓ failed_login_attempts column already exists")
        
        # Add locked_until column if it doesn't exist
        if 'locked_until' not in existing_columns:
            print("Adding locked_until column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN locked_until TIMESTAMP NULL
            """))
            db.commit()
            print("✓ Added locked_until column")
        else:
            print("✓ locked_until column already exists")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_login_lockout_columns()

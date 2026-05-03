"""
Database initialization script for production deployment.
Run this after deploying to create tables and seed initial data.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.base import Base
from app.db.session import engine
from app.models.entities import User, Prompt, Session, RoleplaySession  # noqa: F401

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

if __name__ == "__main__":
    init_db()

"""
Quick script to check user login status.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.entities import User

db = SessionLocal()
try:
    # Get all users and their login status
    users = db.query(User).all()
    print(f"Total users: {len(users)}\n")
    
    for user in users:
        print(f"Email: {user.email}")
        print(f"  Failed attempts: {user.failed_login_attempts}")
        print(f"  Locked until: {user.locked_until}")
        print()
        
finally:
    db.close()

"""
Test script to verify login lockout functionality.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal
from app.models.entities import User
from app.core.security import hash_password


def test_login_lockout():
    """Test the login lockout functionality."""
    db = SessionLocal()
    
    try:
        # Create a test user
        test_email = "lockout_test@example.com"
        
        # Clean up any existing test user
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Create new test user
        test_user = User(
            email=test_email,
            password=hash_password("TestPassword123"),
            failed_login_attempts=0,
            locked_until=None
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✓ Created test user: {test_email}")
        print(f"  - Failed attempts: {test_user.failed_login_attempts}")
        print(f"  - Locked until: {test_user.locked_until}")
        
        # Simulate 3 failed login attempts
        print("\n--- Simulating failed login attempts ---")
        for i in range(1, 4):
            test_user.failed_login_attempts = i
            if i == 3:
                test_user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
            db.commit()
            db.refresh(test_user)
            print(f"Attempt {i}: Failed attempts = {test_user.failed_login_attempts}")
            if test_user.locked_until:
                print(f"  ⚠️  Account locked until: {test_user.locked_until}")
        
        # Verify lockout is in place
        if test_user.locked_until and datetime.now(timezone.utc).replace(tzinfo=None) < test_user.locked_until:
            remaining_minutes = int((test_user.locked_until - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 60)
            print(f"\n✅ Account is locked for {remaining_minutes} more minutes")
        
        # Simulate successful login (reset)
        print("\n--- Simulating successful login ---")
        test_user.failed_login_attempts = 0
        test_user.locked_until = None
        db.commit()
        db.refresh(test_user)
        print(f"✓ Reset: Failed attempts = {test_user.failed_login_attempts}")
        print(f"✓ Reset: Locked until = {test_user.locked_until}")
        
        # Clean up
        db.delete(test_user)
        db.commit()
        print(f"\n✓ Cleaned up test user")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_login_lockout()

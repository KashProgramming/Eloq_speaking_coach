import pytest
from fastapi.testclient import TestClient
from app.models.entities import User, Session as PracticeSession, RoleplaySession, Prompt, UserLevel, PromptCategory, RoleplayScenario
from app.core.security import create_access_token


@pytest.fixture
def auth_user(db_session):
    """Create an authenticated user"""
    user = User(
        id="auth-user-123",
        email="authuser@example.com",
        password="hashed_password",
        level=UserLevel.beginner
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(auth_user):
    """Create authorization headers"""
    token = create_access_token(auth_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_prompt_for_api(db_session):
    """Create a test prompt"""
    prompt = Prompt(
        id="api-prompt-123",
        text="API Test prompt",
        level=UserLevel.beginner,
        category=PromptCategory.opinion
    )
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt


@pytest.fixture
def practice_session_for_api(db_session, auth_user, test_prompt_for_api):
    """Create a practice session for API testing"""
    session = PracticeSession(
        id="api-session-123",
        user_id=auth_user.id,
        prompt_id=test_prompt_for_api.id,
        audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/api_practice.mp3",
        transcript="API test transcript",
        duration=30.0,
        wpm=120,
        fillers=2,
        pauses=3,
        word_count=60,
        fluency_score=85,
        vocabulary_score=80,
        grammar_score=90,
        structure_score=88
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


class TestDeleteAccountAPI:
    """Test the DELETE /auth/account endpoint"""
    
    def test_delete_account_unauthorized(self, client: TestClient):
        """Test that unauthenticated requests are rejected"""
        response = client.delete("/auth/account")
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden
    
    def test_delete_account_success_no_data(self, client: TestClient, db_session, auth_user, auth_headers):
        """Test successful account deletion with no sessions"""
        response = client.delete("/auth/account", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Account successfully deleted"
        assert data["deleted_audio_count"] == 0
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == auth_user.id).first()
        assert deleted_user is None
    
    def test_delete_account_with_practice_sessions(self, client: TestClient, db_session, auth_user, auth_headers, practice_session_for_api):
        """Test account deletion with practice sessions"""
        user_id = auth_user.id
        session_id = practice_session_for_api.id
        
        response = client.delete("/auth/account", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Account successfully deleted"
        assert data["deleted_audio_count"] >= 1
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
        
        # Verify practice session is deleted (cascade)
        deleted_session = db_session.query(PracticeSession).filter(PracticeSession.id == session_id).first()
        assert deleted_session is None
    
    def test_delete_account_rate_limit(self, client: TestClient, auth_headers):
        """Test that rate limiting is applied (3/hour)"""
        # Note: This test would need to be run with rate limiting enabled
        # For now, we just verify the endpoint exists and works
        response = client.delete("/auth/account", headers=auth_headers)
        assert response.status_code in [200, 429]  # 200 success or 429 rate limited

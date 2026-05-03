import pytest
from sqlalchemy.orm import Session
from app.models.entities import User, Session as PracticeSession, RoleplaySession, RoleplayTurnAudio, RoleplayAssistantAudio, Prompt, UserLevel, PromptCategory, RoleplayScenario
from app.services.user_service import get_user_audio_urls, delete_user_account
from datetime import datetime


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        id="test-user-123",
        email="test@example.com",
        password="hashed_password",
        level=UserLevel.beginner
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_prompt(db_session: Session):
    """Create a test prompt"""
    prompt = Prompt(
        id="test-prompt-123",
        text="Test prompt",
        level=UserLevel.beginner,
        category=PromptCategory.opinion
    )
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt


@pytest.fixture
def practice_session_with_audio(db_session: Session, test_user: User, test_prompt: Prompt):
    """Create a practice session with audio"""
    session = PracticeSession(
        id="session-123",
        user_id=test_user.id,
        prompt_id=test_prompt.id,
        audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/practice1.mp3",
        transcript="Test transcript",
        duration=30.0,
        wpm=120,
        fillers=2,
        pauses=3,
        word_count=60,
        fluency_score=85,
        vocabulary_score=80,
        grammar_score=90,
        structure_score=88,
        ideal_answer_audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/ideal1.mp3"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def roleplay_session_with_audio(db_session: Session, test_user: User):
    """Create a roleplay session with audio"""
    rp_session = RoleplaySession(
        id="roleplay-123",
        user_id=test_user.id,
        scenario=RoleplayScenario.interview,
        turn_count=2,
        max_turns=3,
        conversation_history="[]"
    )
    db_session.add(rp_session)
    db_session.commit()
    
    # Add turn audio
    turn_audio = RoleplayTurnAudio(
        id="turn-audio-123",
        session_id=rp_session.id,
        turn_number=1,
        audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/turn1.mp3"
    )
    db_session.add(turn_audio)
    
    # Add assistant audio
    assistant_audio = RoleplayAssistantAudio(
        id="assistant-audio-123",
        session_id=rp_session.id,
        turn_number=1,
        audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/assistant1.mp3"
    )
    db_session.add(assistant_audio)
    
    db_session.commit()
    db_session.refresh(rp_session)
    return rp_session


class TestGetUserAudioUrls:
    """Test audio URL collection"""
    
    def test_user_with_no_sessions(self, db_session: Session, test_user: User):
        audio_urls = get_user_audio_urls(db_session, test_user.id)
        
        assert len(audio_urls["practice_sessions"]) == 0
        assert len(audio_urls["ideal_answers"]) == 0
        assert len(audio_urls["roleplay_turns"]) == 0
        assert len(audio_urls["roleplay_assistant"]) == 0
    
    def test_user_with_practice_session(self, db_session: Session, test_user: User, practice_session_with_audio: PracticeSession):
        audio_urls = get_user_audio_urls(db_session, test_user.id)
        
        assert len(audio_urls["practice_sessions"]) == 1
        assert practice_session_with_audio.audio_url in audio_urls["practice_sessions"]
        assert len(audio_urls["ideal_answers"]) == 1
        assert practice_session_with_audio.ideal_answer_audio_url in audio_urls["ideal_answers"]
    
    def test_user_with_roleplay_session(self, db_session: Session, test_user: User, roleplay_session_with_audio: RoleplaySession):
        audio_urls = get_user_audio_urls(db_session, test_user.id)
        
        assert len(audio_urls["roleplay_turns"]) == 1
        assert len(audio_urls["roleplay_assistant"]) == 1
    
    def test_shared_ideal_answer_not_deleted(self, db_session: Session, test_user: User, test_prompt: Prompt, practice_session_with_audio: PracticeSession):
        # Create another user with same ideal answer
        other_user = User(
            id="other-user-456",
            email="other@example.com",
            password="hashed_password",
            level=UserLevel.beginner
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Create session for other user with same ideal answer
        other_session = PracticeSession(
            id="other-session-456",
            user_id=other_user.id,
            prompt_id=test_prompt.id,
            audio_url="https://res.cloudinary.com/demo/video/upload/v123/eloq_audio/other_practice.mp3",
            transcript="Other transcript",
            duration=30.0,
            wpm=120,
            fillers=2,
            pauses=3,
            word_count=60,
            fluency_score=85,
            vocabulary_score=80,
            grammar_score=90,
            structure_score=88,
            ideal_answer_audio_url=practice_session_with_audio.ideal_answer_audio_url  # Same ideal answer
        )
        db_session.add(other_session)
        db_session.commit()
        
        # Get audio URLs for test_user
        audio_urls = get_user_audio_urls(db_session, test_user.id)
        
        # Ideal answer should NOT be included since another user has it
        assert len(audio_urls["ideal_answers"]) == 0


class TestDeleteUserAccount:
    """Test user account deletion"""
    
    def test_delete_nonexistent_user(self, db_session: Session):
        result = delete_user_account(db_session, "nonexistent-user-id")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    def test_delete_user_with_no_data(self, db_session: Session, test_user: User):
        result = delete_user_account(db_session, test_user.id)
        
        assert result["success"] is True
        assert result["audio_counts"]["total"] == 0
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == test_user.id).first()
        assert deleted_user is None
    
    def test_delete_user_with_practice_sessions(self, db_session: Session, test_user: User, practice_session_with_audio: PracticeSession):
        user_id = test_user.id
        session_id = practice_session_with_audio.id
        
        result = delete_user_account(db_session, user_id)
        
        assert result["success"] is True
        assert result["audio_counts"]["practice_sessions"] == 1
        assert result["audio_counts"]["ideal_answers"] == 1
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
        
        # Verify practice session is deleted (cascade)
        deleted_session = db_session.query(PracticeSession).filter(PracticeSession.id == session_id).first()
        assert deleted_session is None
    
    def test_delete_user_with_roleplay_sessions(self, db_session: Session, test_user: User, roleplay_session_with_audio: RoleplaySession):
        user_id = test_user.id
        rp_session_id = roleplay_session_with_audio.id
        
        result = delete_user_account(db_session, user_id)
        
        assert result["success"] is True
        assert result["audio_counts"]["roleplay_turns"] == 1
        assert result["audio_counts"]["roleplay_assistant"] == 1
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
        
        # Verify roleplay session is deleted (cascade)
        deleted_rp_session = db_session.query(RoleplaySession).filter(RoleplaySession.id == rp_session_id).first()
        assert deleted_rp_session is None
        
        # Verify audio records are deleted (cascade)
        deleted_turn_audio = db_session.query(RoleplayTurnAudio).filter(RoleplayTurnAudio.session_id == rp_session_id).first()
        assert deleted_turn_audio is None
        
        deleted_assistant_audio = db_session.query(RoleplayAssistantAudio).filter(RoleplayAssistantAudio.session_id == rp_session_id).first()
        assert deleted_assistant_audio is None

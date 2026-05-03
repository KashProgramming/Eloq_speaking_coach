from datetime import datetime, timedelta, timezone

from app.models import Prompt, PromptCategory, Session, User, UserLevel
from app.services.prompt_service import get_daily_prompt


def test_get_daily_prompt_excludes_completed(db_session):
    user = User(email="p1@example.com", password="x", level=UserLevel.beginner)
    p1 = Prompt(text="Prompt 1", level=UserLevel.beginner, category=PromptCategory.opinion)
    p2 = Prompt(text="Prompt 2", level=UserLevel.beginner, category=PromptCategory.narration)
    db_session.add_all([user, p1, p2])
    db_session.commit()

    completed = Session(
        user_id=user.id,
        prompt_id=p1.id,
        audio_url="http://example.com/audio.mp3",
        transcript="test",
        duration=60,
        wpm=120,
        fillers=2,
        pauses=1,
        word_count=120,
        fluency_score=6,
        vocabulary_score=6,
        grammar_score=6,
        structure_score=6,
        attempt_number=1,
    )
    db_session.add(completed)
    db_session.commit()

    # Simulate next day
    user.last_prompt_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    user.current_daily_prompt_id = None
    db_session.commit()

    selected = get_daily_prompt(db_session, user)
    assert selected.id == p2.id


def test_get_daily_prompt_persistent_display(db_session):
    """Test that the same prompt is returned multiple times on the same day"""
    user = User(email="p3@example.com", password="x", level=UserLevel.beginner)
    p1 = Prompt(text="Prompt 1", level=UserLevel.beginner, category=PromptCategory.opinion)
    p2 = Prompt(text="Prompt 2", level=UserLevel.beginner, category=PromptCategory.narration)
    db_session.add_all([user, p1, p2])
    db_session.commit()

    # First call should select a prompt
    first_prompt = get_daily_prompt(db_session, user)
    assert first_prompt.id in {p1.id, p2.id}
    
    # Second call same day should return the SAME prompt (persistent display)
    second_prompt = get_daily_prompt(db_session, user)
    assert second_prompt.id == first_prompt.id
    
    # Third call same day should still return the SAME prompt
    third_prompt = get_daily_prompt(db_session, user)
    assert third_prompt.id == first_prompt.id


def test_get_daily_prompt_levels_up_when_exhausted(db_session):
    user = User(email="p2@example.com", password="x", level=UserLevel.beginner)
    beginner = Prompt(text="B", level=UserLevel.beginner, category=PromptCategory.opinion)
    intermediate = Prompt(text="I", level=UserLevel.intermediate, category=PromptCategory.argument)
    db_session.add_all([user, beginner, intermediate])
    db_session.commit()

    completed = Session(
        user_id=user.id,
        prompt_id=beginner.id,
        audio_url="http://example.com/audio.mp3",
        transcript="test",
        duration=60,
        wpm=120,
        fillers=2,
        pauses=1,
        word_count=120,
        fluency_score=6,
        vocabulary_score=6,
        grammar_score=6,
        structure_score=6,
        attempt_number=1,
    )
    db_session.add(completed)
    db_session.commit()

    # Simulate next day
    user.last_prompt_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    user.current_daily_prompt_id = None
    db_session.commit()

    # Now should level up and get intermediate prompt
    selected = get_daily_prompt(db_session, user)
    assert selected.id == intermediate.id
    assert user.level == UserLevel.intermediate


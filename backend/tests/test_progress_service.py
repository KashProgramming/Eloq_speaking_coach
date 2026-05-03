from datetime import datetime, timedelta, timezone

from app.models import Prompt, PromptCategory, Session, User, UserLevel
from app.services.progress_service import calculate_streak, get_progress


def _make_session(user_id: str, prompt_id: str, created_at: datetime, fluency: int = 6):
    return Session(
        user_id=user_id,
        prompt_id=prompt_id,
        audio_url="http://example.com/audio.mp3",
        transcript="test",
        duration=60,
        wpm=120,
        fillers=2,
        pauses=1,
        word_count=120,
        fluency_score=fluency,
        vocabulary_score=6,
        grammar_score=6,
        structure_score=6,
        created_at=created_at,
    )


def test_calculate_streak(db_session):
    user = User(email="progress@example.com", password="x", level=UserLevel.beginner)
    prompt = Prompt(text="P1", level=UserLevel.beginner, category=PromptCategory.opinion)
    db_session.add_all([user, prompt])
    db_session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add_all(
        [
            _make_session(user.id, prompt.id, now, 6),
            _make_session(user.id, prompt.id, now - timedelta(days=1), 7),
            _make_session(user.id, prompt.id, now - timedelta(days=2), 8),
        ]
    )
    db_session.commit()

    assert calculate_streak(db_session, user.id) == 3


def test_get_progress_has_expected_shape(db_session):
    user = User(email="progress2@example.com", password="x", level=UserLevel.beginner)
    prompt = Prompt(text="P2", level=UserLevel.beginner, category=PromptCategory.opinion)
    db_session.add_all([user, prompt])
    db_session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add_all(
        [
            _make_session(user.id, prompt.id, now, 6),
            _make_session(user.id, prompt.id, now - timedelta(days=1), 7),
            _make_session(user.id, prompt.id, now - timedelta(days=8), 5),
        ]
    )
    db_session.commit()

    payload = get_progress(db_session, user, period="week")
    assert "streak" in payload
    assert "weekly_trend" in payload
    assert "improvements" in payload
    assert payload["level"] == "beginner"

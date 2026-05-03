from app.models import Prompt, PromptCategory, Session, User, UserLevel
from app.services.speech_service import ProcessedAudio


def _auth_header(client, email="flow@example.com"):
    client.post("/auth/signup", json={"email": email, "password": "Secure123"})
    login = client.post("/auth/login", json={"email": email, "password": "Secure123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_prompt_endpoint(client, db_session):
    headers = _auth_header(client, "promptflow@example.com")
    db_session.add_all(
        [
            Prompt(text="Prompt A", level=UserLevel.beginner, category=PromptCategory.opinion),
            Prompt(text="Prompt B", level=UserLevel.beginner, category=PromptCategory.narration),
        ]
    )
    db_session.commit()

    res = client.get("/practice/prompt", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["prompt_id"]
    assert data["level"] == "beginner"


def test_analyze_endpoint_happy_path(client, db_session, monkeypatch):
    headers = _auth_header(client, "analyze@example.com")
    prompt = Prompt(text="Should AI be regulated?", level=UserLevel.beginner, category=PromptCategory.argument)
    db_session.add(prompt)
    db_session.commit()

    async def mock_process(*args, **kwargs):
        return ProcessedAudio(
            audio_url="https://cloudinary.com/audio.mp3",
            transcript="I think AI should be regulated carefully",
            duration=60.0,
            segments=[
                {"start": 0.0, "end": 2.0, "text": "I think"},
                {"start": 2.2, "end": 4.0, "text": "AI should"},
            ],
        )

    def mock_eval(*args, **kwargs):
        return {
            "scores": {"fluency": 7, "vocabulary": 6, "grammar": 8, "structure": 6},
            "feedback": ["Good flow"],
            "grammar_mistakes": [],
        }

    monkeypatch.setattr("app.api.practice.process_audio_upload", mock_process)
    monkeypatch.setattr("app.api.practice.evaluate_speech", mock_eval)

    res = client.post(
        "/practice/analyze",
        headers=headers,
        files={"audio_file": ("sample.mp3", b"fake audio", "audio/mpeg")},
        data={"prompt_id": prompt.id},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["session_id"]
    assert body["scores"]["fluency"] == 7


def test_retry_limit_enforced(client, db_session):
    headers = _auth_header(client, "retry@example.com")

    user = db_session.query(User).filter(User.email == "retry@example.com").first()
    assert user is not None

    prompt = Prompt(text="Retry prompt", level=UserLevel.beginner, category=PromptCategory.opinion)
    db_session.add(prompt)
    db_session.commit()

    original = Session(
        user_id=user.id,
        prompt_id=prompt.id,
        audio_url="http://example.com/a.mp3",
        transcript="first",
        duration=60,
        wpm=120,
        fillers=3,
        pauses=2,
        word_count=120,
        fluency_score=5,
        vocabulary_score=5,
        grammar_score=5,
        structure_score=5,
        attempt_number=1,
    )
    db_session.add(original)
    db_session.commit()

    retry2 = Session(
        user_id=user.id,
        prompt_id=prompt.id,
        audio_url="http://example.com/b.mp3",
        transcript="second",
        duration=60,
        wpm=122,
        fillers=2,
        pauses=1,
        word_count=120,
        fluency_score=6,
        vocabulary_score=6,
        grammar_score=6,
        structure_score=6,
        attempt_number=2,
        original_session_id=original.id,
    )
    retry3 = Session(
        user_id=user.id,
        prompt_id=prompt.id,
        audio_url="http://example.com/c.mp3",
        transcript="third",
        duration=60,
        wpm=124,
        fillers=1,
        pauses=1,
        word_count=120,
        fluency_score=7,
        vocabulary_score=7,
        grammar_score=7,
        structure_score=7,
        attempt_number=3,
        original_session_id=original.id,
    )
    db_session.add_all([retry2, retry3])
    db_session.commit()

    res = client.post(
        "/practice/retry",
        headers=headers,
        files={"audio_file": ("sample.mp3", b"fake audio", "audio/mpeg")},
        data={"original_session_id": original.id},
    )
    assert res.status_code == 400
    assert "Maximum retries reached" in res.json()["detail"]


def test_ideal_answer_cached(client, db_session, monkeypatch):
    headers = _auth_header(client, "ideal@example.com")

    user = db_session.query(User).filter(User.email == "ideal@example.com").first()
    assert user is not None
    prompt = Prompt(text="Ideal prompt", level=UserLevel.beginner, category=PromptCategory.explanation)
    db_session.add(prompt)
    db_session.commit()

    practice_session = Session(
        user_id=user.id,
        prompt_id=prompt.id,
        audio_url="http://example.com/a.mp3",
        transcript="my raw transcript",
        duration=60,
        wpm=120,
        fillers=2,
        pauses=1,
        word_count=120,
        fluency_score=6,
        vocabulary_score=6,
        grammar_score=6,
        structure_score=6,
    )
    db_session.add(practice_session)
    db_session.commit()

    calls = {"count": 0}

    def mock_ideal(*args, **kwargs):
        calls["count"] += 1
        return "Polished answer"

    monkeypatch.setattr("app.api.practice.generate_ideal_answer", mock_ideal)

    first = client.get(f"/practice/session/{practice_session.id}/ideal-answer", headers=headers)
    second = client.get(f"/practice/session/{practice_session.id}/ideal-answer", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["ideal_answer"] == "Polished answer"
    assert second.json()["ideal_answer"] == "Polished answer"
    assert calls["count"] == 1


def test_roleplay_three_turn_flow(client, monkeypatch):
    headers = _auth_header(client, "roleplay@example.com")

    monkeypatch.setattr(
        "app.api.roleplay.generate_roleplay_opening_question",
        lambda scenario: "Tell me about yourself.",
    )

    start = client.post("/roleplay/start", headers=headers, json={"scenario": "interview"})
    assert start.status_code == 200
    roleplay_session_id = start.json()["session_id"]

    transcripts = iter(["Response one", "Response two", "Response three"])

    async def mock_process(*args, **kwargs):
        return ProcessedAudio(
            audio_url="https://cloudinary.com/audio.mp3",
            transcript=next(transcripts),
            duration=20.0,
            segments=[{"start": 0.0, "end": 1.0, "text": "ok"}],
        )

    monkeypatch.setattr("app.api.roleplay.process_audio_upload", mock_process)
    monkeypatch.setattr(
        "app.api.roleplay.evaluate_roleplay_response",
        lambda *args, **kwargs: {
            "scores": {"fluency": 7, "vocabulary": 6, "grammar": 8, "structure": 7},
            "strengths": ["Clear"],
            "weaknesses": ["Need examples"],
        },
    )
    monkeypatch.setattr(
        "app.api.roleplay.generate_roleplay_followup_question",
        lambda *args, **kwargs: "Can you give a concrete example?",
    )
    monkeypatch.setattr(
        "app.api.roleplay.generate_roleplay_final_summary",
        lambda *args, **kwargs: {
            "strengths": ["Consistent communication"],
            "areas_to_improve": ["Add more metrics"],
            "overall_score": 7,
            "avg_fluency": 7,
            "avg_vocabulary": 6,
            "avg_grammar": 8,
            "avg_structure": 7,
        },
    )

    r1 = client.post(
        "/roleplay/respond",
        headers=headers,
        files={"audio_file": ("r1.mp3", b"a", "audio/mpeg")},
        data={"session_id": roleplay_session_id},
    )
    assert r1.status_code == 200
    assert r1.json()["is_final_turn"] is False

    r2 = client.post(
        "/roleplay/respond",
        headers=headers,
        files={"audio_file": ("r2.mp3", b"a", "audio/mpeg")},
        data={"session_id": roleplay_session_id},
    )
    assert r2.status_code == 200
    assert r2.json()["is_final_turn"] is False

    r3 = client.post(
        "/roleplay/respond",
        headers=headers,
        files={"audio_file": ("r3.mp3", b"a", "audio/mpeg")},
        data={"session_id": roleplay_session_id},
    )
    assert r3.status_code == 200
    assert r3.json()["is_final_turn"] is True
    assert r3.json()["overall_summary"]["overall_score"] == 7

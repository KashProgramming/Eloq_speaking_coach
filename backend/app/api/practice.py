from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models import Prompt, Session as PracticeSession, User
from typing import Union

from app.schemas.analysis import (
    AnalyzeResponse,
    AttemptSnapshot,
    IdealAnswerResponse,
    MetricsResponse,
    RetryComparison,
    RetryResponse,
    ScoresResponse,
)
from app.schemas.progress import ProgressResponse
from app.schemas.prompt import (
    AttemptSummary,
    GroupedPracticeHistoryResponse,
    GroupedPracticeSession,
    PracticeHistoryResponse,
    PracticeSessionHistoryItem,
    PromptResponse,
)
from app.services.llm_service import evaluate_speech, generate_ideal_answer
from app.services.metrics_service import compute_metrics
from app.services.progress_service import get_progress
from app.services.prompt_service import get_daily_prompt
from app.services.speech_service import process_audio_upload
from app.services.tts_service import generate_speech

router = APIRouter(prefix="/practice", tags=["practice"])


def _session_to_response(session: PracticeSession, feedback: list[str], grammar_mistakes: list[str]) -> AnalyzeResponse:
    return AnalyzeResponse(
        session_id=session.id,
        audio_url=session.audio_url,
        transcript=session.transcript,
        duration=session.duration,
        metrics=MetricsResponse(
            wpm=session.wpm,
            fillers=session.fillers,
            pauses=session.pauses,
            word_count=session.word_count,
        ),
        scores=ScoresResponse(
            fluency=session.fluency_score,
            vocabulary=session.vocabulary_score,
            grammar=session.grammar_score,
            structure=session.structure_score,
        ),
        feedback=feedback,
        grammar_mistakes=grammar_mistakes,
    )


@router.get("/prompt", response_model=PromptResponse)
def fetch_prompt(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        prompt = get_daily_prompt(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PromptResponse(
        prompt_id=prompt.id,
        level=prompt.level.value,
        category=prompt.category.value,
        text=prompt.text,
    )


@router.post("/analyze", response_model=Union[AnalyzeResponse, RetryResponse])
@limiter.limit("10/hour")
async def analyze_audio(
    request: Request,
    audio_file: UploadFile = File(...),
    prompt_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid prompt_id")

    # Check if user already has a session for this prompt today
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    today_start = datetime.now(ZoneInfo("Asia/Kolkata")).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    today_end = today_start + timedelta(days=1)
    
    existing_session = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.user_id == current_user.id,
            PracticeSession.prompt_id == prompt_id,
            PracticeSession.attempt_number == 1,
            PracticeSession.created_at >= today_start,
            PracticeSession.created_at < today_end,
        )
        .first()
    )

    # If existing session found, treat this as a retry
    if existing_session:
        # Check retry limit
        existing_attempts = (
            db.query(PracticeSession)
            .filter(
                (PracticeSession.id == existing_session.id)
                | (PracticeSession.original_session_id == existing_session.id)
            )
            .count()
        )
        if existing_attempts >= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum retries reached (3 attempts per prompt per day)")

        # Process audio and create retry session
        processed = await process_audio_upload(audio_file, enforce_duration_bounds=True)
        metrics = compute_metrics(processed.transcript, processed.duration, processed.segments)
        evaluation = evaluate_speech(
            transcript=processed.transcript,
            metrics=metrics,
            prompt_text=prompt.text,
            user_level=current_user.level.value,
        )

        import json

        retry_session = PracticeSession(
            user_id=current_user.id,
            prompt_id=prompt.id,
            audio_url=processed.audio_url,
            transcript=processed.transcript,
            duration=metrics["duration"],
            wpm=metrics["wpm"],
            fillers=metrics["fillers"],
            pauses=metrics["pauses"],
            word_count=metrics["word_count"],
            fluency_score=evaluation["scores"]["fluency"],
            vocabulary_score=evaluation["scores"]["vocabulary"],
            grammar_score=evaluation["scores"]["grammar"],
            structure_score=evaluation["scores"]["structure"],
            feedback=json.dumps(evaluation["feedback"]),
            grammar_mistakes=json.dumps(evaluation["grammar_mistakes"]),
            attempt_number=existing_attempts + 1,
            original_session_id=existing_session.id,
        )
        db.add(retry_session)
        db.commit()
        db.refresh(retry_session)

        # Return retry response with comparison
        base_response = _session_to_response(retry_session, evaluation["feedback"], evaluation["grammar_mistakes"])

        comparison = RetryComparison(
            original_attempt=AttemptSnapshot(
                wpm=existing_session.wpm,
                fillers=existing_session.fillers,
                pauses=existing_session.pauses,
                fluency_score=existing_session.fluency_score,
            ),
            current_attempt=AttemptSnapshot(
                wpm=retry_session.wpm,
                fillers=retry_session.fillers,
                pauses=retry_session.pauses,
                fluency_score=retry_session.fluency_score,
            ),
            improvements={
                "wpm": f"{retry_session.wpm - existing_session.wpm:+.1f}",
                "fillers": f"{retry_session.fillers - existing_session.fillers:+d}",
                "pauses": f"{retry_session.pauses - existing_session.pauses:+d}",
                "fluency_score": f"{retry_session.fluency_score - existing_session.fluency_score:+d}",
            },
        )

        return RetryResponse(**base_response.model_dump(), comparison=comparison)

    # No existing session - create first attempt
    processed = await process_audio_upload(audio_file, enforce_duration_bounds=True)
    metrics = compute_metrics(processed.transcript, processed.duration, processed.segments)
    evaluation = evaluate_speech(
        transcript=processed.transcript,
        metrics=metrics,
        prompt_text=prompt.text,
        user_level=current_user.level.value,
    )

    import json

    session = PracticeSession(
        user_id=current_user.id,
        prompt_id=prompt.id,
        audio_url=processed.audio_url,
        transcript=processed.transcript,
        duration=metrics["duration"],
        wpm=metrics["wpm"],
        fillers=metrics["fillers"],
        pauses=metrics["pauses"],
        word_count=metrics["word_count"],
        fluency_score=evaluation["scores"]["fluency"],
        vocabulary_score=evaluation["scores"]["vocabulary"],
        grammar_score=evaluation["scores"]["grammar"],
        structure_score=evaluation["scores"]["structure"],
        feedback=json.dumps(evaluation["feedback"]),
        grammar_mistakes=json.dumps(evaluation["grammar_mistakes"]),
        attempt_number=1,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return _session_to_response(session, evaluation["feedback"], evaluation["grammar_mistakes"])


@router.get("/session/{session_id}/ideal-answer", response_model=IdealAnswerResponse)
def get_ideal_answer(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(PracticeSession)
        .join(Prompt, PracticeSession.prompt_id == Prompt.id)
        .filter(PracticeSession.id == session_id, PracticeSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Generate ideal answer if not exists
    if not session.ideal_answer:
        prompt = db.query(Prompt).filter(Prompt.id == session.prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

        ideal_answer = generate_ideal_answer(session.transcript, prompt.text, current_user.level.value)
        session.ideal_answer = ideal_answer
        db.commit()
    
    # Generate TTS audio if not exists (optional - don't fail if TTS unavailable)
    if not session.ideal_answer_audio_url:
        try:
            audio_url = generate_speech(session.ideal_answer)
            session.ideal_answer_audio_url = audio_url
            db.commit()
        except Exception as e:
            # Log error but don't fail the request - TTS is optional
            print(f"TTS generation failed (continuing without audio): {e}")
            # Ensure audio_url is None if generation failed
            session.ideal_answer_audio_url = None

    return IdealAnswerResponse(
        ideal_answer=session.ideal_answer,
        ideal_answer_audio_url=session.ideal_answer_audio_url
    )


@router.post("/retry", response_model=RetryResponse)
async def retry_prompt(
    audio_file: UploadFile = File(...),
    original_session_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    original_session = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.id == original_session_id,
            PracticeSession.user_id == current_user.id,
            PracticeSession.attempt_number == 1,
        )
        .first()
    )
    if not original_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original session not found")

    existing_attempts = (
        db.query(PracticeSession)
        .filter(
            (PracticeSession.id == original_session.id)
            | (PracticeSession.original_session_id == original_session.id)
        )
        .count()
    )
    if existing_attempts >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum retries reached")

    prompt = db.query(Prompt).filter(Prompt.id == original_session.prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    processed = await process_audio_upload(audio_file, enforce_duration_bounds=True)
    metrics = compute_metrics(processed.transcript, processed.duration, processed.segments)
    evaluation = evaluate_speech(
        transcript=processed.transcript,
        metrics=metrics,
        prompt_text=prompt.text,
        user_level=current_user.level.value,
    )

    import json

    retry_session = PracticeSession(
        user_id=current_user.id,
        prompt_id=prompt.id,
        audio_url=processed.audio_url,
        transcript=processed.transcript,
        duration=metrics["duration"],
        wpm=metrics["wpm"],
        fillers=metrics["fillers"],
        pauses=metrics["pauses"],
        word_count=metrics["word_count"],
        fluency_score=evaluation["scores"]["fluency"],
        vocabulary_score=evaluation["scores"]["vocabulary"],
        grammar_score=evaluation["scores"]["grammar"],
        structure_score=evaluation["scores"]["structure"],
        feedback=json.dumps(evaluation["feedback"]),
        grammar_mistakes=json.dumps(evaluation["grammar_mistakes"]),
        attempt_number=existing_attempts + 1,
        original_session_id=original_session.id,
    )
    db.add(retry_session)
    db.commit()
    db.refresh(retry_session)

    base_response = _session_to_response(retry_session, evaluation["feedback"], evaluation["grammar_mistakes"])

    comparison = RetryComparison(
        original_attempt=AttemptSnapshot(
            wpm=original_session.wpm,
            fillers=original_session.fillers,
            pauses=original_session.pauses,
            fluency_score=original_session.fluency_score,
        ),
        current_attempt=AttemptSnapshot(
            wpm=retry_session.wpm,
            fillers=retry_session.fillers,
            pauses=retry_session.pauses,
            fluency_score=retry_session.fluency_score,
        ),
        improvements={
            "wpm": f"{retry_session.wpm - original_session.wpm:+.1f}",
            "fillers": f"{retry_session.fillers - original_session.fillers:+d}",
            "pauses": f"{retry_session.pauses - original_session.pauses:+d}",
            "fluency_score": f"{retry_session.fluency_score - original_session.fluency_score:+d}",
        },
    )

    return RetryResponse(**base_response.model_dump(), comparison=comparison)


@router.get("/progress", response_model=ProgressResponse)
@limiter.limit("100/hour")
def progress(
    request: Request,
    period: str = Query(default="week", pattern="^(week|month|all)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = get_progress(db, current_user, period)
    return ProgressResponse(**payload)


@router.get("/history", response_model=PracticeHistoryResponse)
def get_practice_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's practice session history with pagination."""
    import json

    # Get total count
    total = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == current_user.id, PracticeSession.attempt_number == 1)
        .count()
    )

    # Get sessions with prompts
    sessions = (
        db.query(PracticeSession, Prompt)
        .join(Prompt, PracticeSession.prompt_id == Prompt.id)
        .filter(PracticeSession.user_id == current_user.id, PracticeSession.attempt_number == 1)
        .order_by(PracticeSession.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    history_items = [
        PracticeSessionHistoryItem(
            session_id=session.id,
            prompt_text=prompt.text,
            prompt_category=prompt.category.value,
            audio_url=session.audio_url,
            transcript=session.transcript,
            duration=session.duration,
            wpm=session.wpm,
            fillers=session.fillers,
            pauses=session.pauses,
            word_count=session.word_count,
            fluency_score=session.fluency_score,
            vocabulary_score=session.vocabulary_score,
            grammar_score=session.grammar_score,
            structure_score=session.structure_score,
            ideal_answer=session.ideal_answer,
            ideal_answer_audio_url=session.ideal_answer_audio_url,
            feedback=json.loads(session.feedback) if session.feedback else None,
            grammar_mistakes=json.loads(session.grammar_mistakes) if session.grammar_mistakes else None,
            created_at=session.created_at,
        )
        for session, prompt in sessions
    ]

    return PracticeHistoryResponse(sessions=history_items, total=total)


@router.get("/history/grouped", response_model=GroupedPracticeHistoryResponse)
def get_grouped_practice_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's practice session history grouped by prompt with all attempts."""
    from collections import defaultdict
    
    # Get all original sessions (attempt_number=1) with pagination
    original_sessions = (
        db.query(PracticeSession, Prompt)
        .join(Prompt, PracticeSession.prompt_id == Prompt.id)
        .filter(PracticeSession.user_id == current_user.id, PracticeSession.attempt_number == 1)
        .order_by(PracticeSession.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    # Get total count
    total = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == current_user.id, PracticeSession.attempt_number == 1)
        .count()
    )
    
    # For each original session, get all retry attempts
    grouped_sessions = []
    for original_session, prompt in original_sessions:
        # Get all attempts (original + retries)
        all_attempts = (
            db.query(PracticeSession)
            .filter(
                (PracticeSession.id == original_session.id)
                | (PracticeSession.original_session_id == original_session.id)
            )
            .order_by(PracticeSession.attempt_number)
            .all()
        )
        
        # Create attempt summaries
        attempt_summaries = [
            AttemptSummary(
                session_id=attempt.id,
                attempt_number=attempt.attempt_number,
                created_at=attempt.created_at,
                fluency_score=attempt.fluency_score,
                vocabulary_score=attempt.vocabulary_score,
                grammar_score=attempt.grammar_score,
                structure_score=attempt.structure_score,
                wpm=attempt.wpm,
                fillers=attempt.fillers,
                pauses=attempt.pauses,
            )
            for attempt in all_attempts
        ]
        
        # Group by date (use the original session's date)
        date_str = original_session.created_at.strftime("%Y-%m-%d")
        
        grouped_sessions.append(
            GroupedPracticeSession(
                prompt_text=prompt.text,
                prompt_category=prompt.category.value,
                date=date_str,
                attempts=attempt_summaries,
            )
        )
    
    return GroupedPracticeHistoryResponse(sessions=grouped_sessions, total=total)


@router.get("/session/{session_id}", response_model=PracticeSessionHistoryItem)
def get_practice_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific practice session."""
    import json

    result = (
        db.query(PracticeSession, Prompt)
        .join(Prompt, PracticeSession.prompt_id == Prompt.id)
        .filter(PracticeSession.id == session_id, PracticeSession.user_id == current_user.id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session, prompt = result

    return PracticeSessionHistoryItem(
        session_id=session.id,
        prompt_text=prompt.text,
        prompt_category=prompt.category.value,
        audio_url=session.audio_url,
        transcript=session.transcript,
        duration=session.duration,
        wpm=session.wpm,
        fillers=session.fillers,
        pauses=session.pauses,
        word_count=session.word_count,
        fluency_score=session.fluency_score,
        vocabulary_score=session.vocabulary_score,
        grammar_score=session.grammar_score,
        structure_score=session.structure_score,
        ideal_answer=session.ideal_answer,
        ideal_answer_audio_url=session.ideal_answer_audio_url,
        feedback=json.loads(session.feedback) if session.feedback else None,
        grammar_mistakes=json.loads(session.grammar_mistakes) if session.grammar_mistakes else None,
        created_at=session.created_at,
    )

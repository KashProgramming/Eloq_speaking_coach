import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models import RoleplayScenario, RoleplaySession, RoleplayTurnAudio, RoleplayAssistantAudio, RoleplayTurnMetrics, User
from app.schemas.roleplay import (
    ConversationTurn,
    RoleplayHistoryResponse,
    RoleplayOverallSummary,
    RoleplayRespondResponse,
    RoleplaySessionHistoryItem,
    RoleplaySessionsListResponse,
    RoleplayStartRequest,
    RoleplayStartResponse,
    TurnEvaluation,
)
from app.services.llm_service import (
    evaluate_roleplay_response,
    generate_roleplay_final_summary,
    generate_roleplay_followup_question,
    generate_roleplay_opening_question,
)
from app.services.metrics_service import compute_metrics
from app.services.speech_service import process_audio_upload
from app.services.tts_service import generate_speech

router = APIRouter(prefix="/roleplay", tags=["roleplay"])


@router.post("/start", response_model=RoleplayStartResponse)
def start_roleplay(
    payload: RoleplayStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        scenario = RoleplayScenario(payload.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid scenario") from exc

    opening_question = generate_roleplay_opening_question(scenario.value)
    history = [{"role": "assistant", "content": opening_question}]

    roleplay_session = RoleplaySession(
        user_id=current_user.id,
        scenario=scenario,
        turn_count=0,
        max_turns=3,
        conversation_history=json.dumps(history),
    )
    db.add(roleplay_session)
    db.commit()
    db.refresh(roleplay_session)

    # Generate TTS for opening question (optional - don't fail if TTS unavailable)
    audio_url = None
    try:
        audio_url = generate_speech(opening_question)
        assistant_audio = RoleplayAssistantAudio(
            session_id=roleplay_session.id,
            turn_number=0,
            audio_url=audio_url,
        )
        db.add(assistant_audio)
        db.commit()
    except Exception as e:
        # Log error but don't fail the request - TTS is optional
        print(f"TTS generation failed for opening question (continuing without audio): {e}")
        audio_url = None

    return RoleplayStartResponse(
        session_id=roleplay_session.id,
        scenario=scenario.value,
        opening_question=opening_question,
        turn_count=roleplay_session.turn_count,
        max_turns=roleplay_session.max_turns,
        audio_url=audio_url,
    )


@router.post("/respond", response_model=RoleplayRespondResponse)
async def respond_roleplay(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roleplay_session = (
        db.query(RoleplaySession)
        .filter(RoleplaySession.id == session_id, RoleplaySession.user_id == current_user.id)
        .first()
    )
    if not roleplay_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roleplay session not found")

    if roleplay_session.completed_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Roleplay session already completed")

    history = json.loads(roleplay_session.conversation_history)
    processed = await process_audio_upload(audio_file, enforce_duration_bounds=False)
    
    # Compute metrics
    metrics = compute_metrics(processed.transcript, processed.duration, processed.segments)
    
    # Evaluate with comprehensive metrics
    evaluation = evaluate_roleplay_response(
        roleplay_session.scenario.value, 
        processed.transcript,
        metrics,
        current_user.level.value
    )

    history.append({"role": "user", "content": processed.transcript})
    next_turn = roleplay_session.turn_count + 1
    roleplay_session.turn_count = next_turn

    # Store audio URL for this turn
    turn_audio = RoleplayTurnAudio(
        session_id=session_id,
        turn_number=next_turn,
        audio_url=processed.audio_url,
    )
    db.add(turn_audio)
    
    # Store turn metrics
    turn_metrics = RoleplayTurnMetrics(
        session_id=session_id,
        turn_number=next_turn,
        transcript=processed.transcript,
        duration=processed.duration,
        wpm=metrics["wpm"],
        fillers=metrics["fillers"],
        pauses=metrics["pauses"],
        word_count=metrics["word_count"],
        fluency_score=evaluation["scores"]["fluency"],
        vocabulary_score=evaluation["scores"]["vocabulary"],
        grammar_score=evaluation["scores"]["grammar"],
        structure_score=evaluation["scores"]["structure"],
        strengths=json.dumps(evaluation["strengths"]),
        weaknesses=json.dumps(evaluation["weaknesses"]),
    )
    db.add(turn_metrics)

    is_final_turn = next_turn >= roleplay_session.max_turns
    if is_final_turn:
        # Get all turn metrics for averaging
        all_turn_metrics = (
            db.query(RoleplayTurnMetrics)
            .filter(RoleplayTurnMetrics.session_id == session_id)
            .all()
        )
        # Include current turn
        all_turn_metrics.append(turn_metrics)
        
        turn_metrics_data = [
            {
                "fluency_score": tm.fluency_score,
                "vocabulary_score": tm.vocabulary_score,
                "grammar_score": tm.grammar_score,
                "structure_score": tm.structure_score,
            }
            for tm in all_turn_metrics
        ]
        
        summary = generate_roleplay_final_summary(
            roleplay_session.scenario.value, 
            history,
            turn_metrics_data
        )
        
        roleplay_session.overall_score = summary["overall_score"]
        roleplay_session.strengths = json.dumps(summary["strengths"])
        roleplay_session.areas_to_improve = json.dumps(summary["areas_to_improve"])
        roleplay_session.fluency_score = summary["avg_fluency"]
        roleplay_session.vocabulary_score = summary["avg_vocabulary"]
        roleplay_session.grammar_score = summary["avg_grammar"]
        roleplay_session.structure_score = summary["avg_structure"]
        roleplay_session.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        roleplay_session.conversation_history = json.dumps(history)
        db.commit()

        return RoleplayRespondResponse(
            transcript=processed.transcript,
            evaluation=TurnEvaluation(
                strengths=evaluation["strengths"],
                weaknesses=evaluation["weaknesses"],
                scores=evaluation["scores"]
            ),
            turn_count=roleplay_session.turn_count,
            is_final_turn=True,
            overall_summary=RoleplayOverallSummary(**summary),
        )

    follow_up = generate_roleplay_followup_question(
        scenario=roleplay_session.scenario.value,
        turn_count=next_turn,
        max_turns=roleplay_session.max_turns,
        history=history,
        transcript=processed.transcript,
    )

    history.append({"role": "assistant", "content": follow_up})
    roleplay_session.conversation_history = json.dumps(history)
    db.commit()

    # Generate TTS for follow-up question (optional - don't fail if TTS unavailable)
    follow_up_audio_url = None
    try:
        follow_up_audio_url = generate_speech(follow_up)
        assistant_audio = RoleplayAssistantAudio(
            session_id=session_id,
            turn_number=next_turn,
            audio_url=follow_up_audio_url,
        )
        db.add(assistant_audio)
        db.commit()
    except Exception as e:
        # Log error but don't fail the request - TTS is optional
        print(f"TTS generation failed for follow-up question (continuing without audio): {e}")
        follow_up_audio_url = None

    return RoleplayRespondResponse(
        transcript=processed.transcript,
        evaluation=TurnEvaluation(
            strengths=evaluation["strengths"],
            weaknesses=evaluation["weaknesses"],
            scores=evaluation["scores"]
        ),
        follow_up_question=follow_up,
        follow_up_audio_url=follow_up_audio_url,
        turn_count=roleplay_session.turn_count,
        is_final_turn=False,
    )


@router.get("/{session_id}/history", response_model=RoleplayHistoryResponse)
def roleplay_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roleplay_session = (
        db.query(RoleplaySession)
        .filter(RoleplaySession.id == session_id, RoleplaySession.user_id == current_user.id)
        .first()
    )
    if not roleplay_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roleplay session not found")

    return RoleplayHistoryResponse(
        session_id=roleplay_session.id,
        scenario=roleplay_session.scenario.value,
        turn_count=roleplay_session.turn_count,
        max_turns=roleplay_session.max_turns,
        history=json.loads(roleplay_session.conversation_history),
    )


@router.get("/sessions/list", response_model=RoleplaySessionsListResponse)
def get_roleplay_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's roleplay session history with pagination."""
    # Get total count
    total = db.query(RoleplaySession).filter(RoleplaySession.user_id == current_user.id).count()

    # Get sessions
    sessions = (
        db.query(RoleplaySession)
        .filter(RoleplaySession.user_id == current_user.id)
        .order_by(RoleplaySession.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    history_items = []
    for session in sessions:
        # Get audio URLs for this session (user turns)
        turn_audios = (
            db.query(RoleplayTurnAudio)
            .filter(RoleplayTurnAudio.session_id == session.id)
            .order_by(RoleplayTurnAudio.turn_number)
            .all()
        )
        audio_map = {audio.turn_number: audio.audio_url for audio in turn_audios}

        # Get assistant audio URLs
        assistant_audios = (
            db.query(RoleplayAssistantAudio)
            .filter(RoleplayAssistantAudio.session_id == session.id)
            .order_by(RoleplayAssistantAudio.turn_number)
            .all()
        )
        assistant_audio_map = {audio.turn_number: audio.audio_url for audio in assistant_audios}

        # Parse conversation history and add audio URLs
        conversation = json.loads(session.conversation_history)
        conversation_with_audio = []
        user_turn_number = 0
        assistant_turn_number = 0

        for turn in conversation:
            audio_url = None
            if turn["role"] == "user":
                user_turn_number += 1
                audio_url = audio_map.get(user_turn_number)
            elif turn["role"] == "assistant":
                audio_url = assistant_audio_map.get(assistant_turn_number)
                assistant_turn_number += 1

            conversation_with_audio.append(
                ConversationTurn(role=turn["role"], content=turn["content"], audio_url=audio_url)
            )

        history_items.append(
            RoleplaySessionHistoryItem(
                session_id=session.id,
                scenario=session.scenario.value,
                turn_count=session.turn_count,
                max_turns=session.max_turns,
                overall_score=session.overall_score,
                strengths=json.loads(session.strengths) if session.strengths else None,
                areas_to_improve=json.loads(session.areas_to_improve) if session.areas_to_improve else None,
                fluency_score=session.fluency_score,
                vocabulary_score=session.vocabulary_score,
                grammar_score=session.grammar_score,
                structure_score=session.structure_score,
                created_at=session.created_at,
                completed_at=session.completed_at,
                conversation_history=conversation_with_audio,
            )
        )

    return RoleplaySessionsListResponse(sessions=history_items, total=total)


@router.get("/sessions/{session_id}", response_model=RoleplaySessionHistoryItem)
def get_roleplay_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific roleplay session."""
    session = (
        db.query(RoleplaySession)
        .filter(RoleplaySession.id == session_id, RoleplaySession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Get audio URLs for this session (user turns)
    turn_audios = (
        db.query(RoleplayTurnAudio)
        .filter(RoleplayTurnAudio.session_id == session.id)
        .order_by(RoleplayTurnAudio.turn_number)
        .all()
    )
    audio_map = {audio.turn_number: audio.audio_url for audio in turn_audios}

    # Get assistant audio URLs
    assistant_audios = (
        db.query(RoleplayAssistantAudio)
        .filter(RoleplayAssistantAudio.session_id == session.id)
        .order_by(RoleplayAssistantAudio.turn_number)
        .all()
    )
    assistant_audio_map = {audio.turn_number: audio.audio_url for audio in assistant_audios}

    # Parse conversation history and add audio URLs
    conversation = json.loads(session.conversation_history)
    conversation_with_audio = []
    user_turn_number = 0
    assistant_turn_number = 0

    for turn in conversation:
        audio_url = None
        if turn["role"] == "user":
            user_turn_number += 1
            audio_url = audio_map.get(user_turn_number)
        elif turn["role"] == "assistant":
            audio_url = assistant_audio_map.get(assistant_turn_number)
            assistant_turn_number += 1

        conversation_with_audio.append(
            ConversationTurn(role=turn["role"], content=turn["content"], audio_url=audio_url)
        )

    return RoleplaySessionHistoryItem(
        session_id=session.id,
        scenario=session.scenario.value,
        turn_count=session.turn_count,
        max_turns=session.max_turns,
        overall_score=session.overall_score,
        strengths=json.loads(session.strengths) if session.strengths else None,
        areas_to_improve=json.loads(session.areas_to_improve) if session.areas_to_improve else None,
        fluency_score=session.fluency_score,
        vocabulary_score=session.vocabulary_score,
        grammar_score=session.grammar_score,
        structure_score=session.structure_score,
        created_at=session.created_at,
        completed_at=session.completed_at,
        conversation_history=conversation_with_audio,
    )

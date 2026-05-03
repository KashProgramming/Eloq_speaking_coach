from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.models.entities import User, Session as PracticeSession, RoleplaySession, RoleplayTurnAudio, RoleplayAssistantAudio
from app.services.storage_service import delete_multiple_audios


def get_user_audio_urls(db: Session, user_id: str) -> dict[str, list[str]]:
    """
    Collect all audio URLs associated with a user.
    Returns a dict with categorized audio URLs.
    """
    audio_urls = {
        "practice_sessions": [],
        "ideal_answers": [],
        "roleplay_turns": [],
        "roleplay_assistant": []
    }
    
    # Get practice session audio URLs
    practice_sessions = db.query(PracticeSession).filter(
        PracticeSession.user_id == user_id
    ).all()
    
    for session in practice_sessions:
        if session.audio_url:
            audio_urls["practice_sessions"].append(session.audio_url)
        
        # Collect ideal answer audio URLs (check if unique to this user)
        if session.ideal_answer_audio_url:
            # Check if any other user has a session with the same ideal answer audio
            other_user_has_same = db.query(PracticeSession).filter(
                PracticeSession.user_id != user_id,
                PracticeSession.ideal_answer_audio_url == session.ideal_answer_audio_url
            ).first()
            
            # Only add if unique to this user
            if not other_user_has_same and session.ideal_answer_audio_url not in audio_urls["ideal_answers"]:
                audio_urls["ideal_answers"].append(session.ideal_answer_audio_url)
    
    # Get roleplay session audio URLs
    roleplay_sessions = db.query(RoleplaySession).filter(
        RoleplaySession.user_id == user_id
    ).all()
    
    for rp_session in roleplay_sessions:
        # Get turn audio
        turn_audios = db.query(RoleplayTurnAudio).filter(
            RoleplayTurnAudio.session_id == rp_session.id
        ).all()
        for turn_audio in turn_audios:
            if turn_audio.audio_url:
                audio_urls["roleplay_turns"].append(turn_audio.audio_url)
        
        # Get assistant audio
        assistant_audios = db.query(RoleplayAssistantAudio).filter(
            RoleplayAssistantAudio.session_id == rp_session.id
        ).all()
        for assistant_audio in assistant_audios:
            if assistant_audio.audio_url:
                audio_urls["roleplay_assistant"].append(assistant_audio.audio_url)
    
    return audio_urls


def delete_user_account(db: Session, user_id: str) -> dict:
    """
    Delete a user account and all associated data.
    
    Steps:
    1. Collect all audio URLs
    2. Delete audio files from Cloudinary
    3. Delete user from database (cascade handles related records)
    
    Returns a dict with deletion results.
    """
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "User not found"}
    
    # Collect all audio URLs
    audio_urls = get_user_audio_urls(db, user_id)
    
    # Flatten all audio URLs for deletion
    all_audio_urls = (
        audio_urls["practice_sessions"] +
        audio_urls["ideal_answers"] +
        audio_urls["roleplay_turns"] +
        audio_urls["roleplay_assistant"]
    )
    
    # Delete audio files from Cloudinary
    cloudinary_results = delete_multiple_audios(all_audio_urls)
    
    # Delete user from database (cascade will handle related records)
    try:
        db.delete(user)
        db.commit()
        
        return {
            "success": True,
            "user_id": user_id,
            "audio_deletion": cloudinary_results,
            "audio_counts": {
                "practice_sessions": len(audio_urls["practice_sessions"]),
                "ideal_answers": len(audio_urls["ideal_answers"]),
                "roleplay_turns": len(audio_urls["roleplay_turns"]),
                "roleplay_assistant": len(audio_urls["roleplay_assistant"]),
                "total": len(all_audio_urls)
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Database deletion failed: {str(e)}",
            "audio_deletion": cloudinary_results
        }

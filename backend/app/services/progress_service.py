from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import Prompt, RoleplaySession, Session as PracticeSession, User


def calculate_streak(db: Session, user_id: str) -> int:
    """Calculate streak based on both practice and roleplay sessions."""
    practice_sessions = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user_id)
        .order_by(PracticeSession.created_at.desc())
        .all()
    )
    
    roleplay_sessions = (
        db.query(RoleplaySession)
        .filter(RoleplaySession.user_id == user_id)
        .order_by(RoleplaySession.created_at.desc())
        .all()
    )
    
    # Combine all session dates
    all_dates = set()
    for s in practice_sessions:
        all_dates.add(s.created_at.date())
    for s in roleplay_sessions:
        all_dates.add(s.created_at.date())

    if not all_dates:
        return 0

    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    session_dates = sorted(all_dates, reverse=True)

    if session_dates[0] != today:
        return 0

    streak = 1
    for i in range(len(session_dates) - 1):
        if (session_dates[i] - session_dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def _period_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    if period == "month":
        return now - timedelta(days=30), now
    if period == "all":
        return datetime.min, now
    return now - timedelta(days=7), now


def _avg(sessions: list[PracticeSession], field: str) -> float:
    if not sessions:
        return 0.0
    return sum(getattr(s, field) for s in sessions) / len(sessions)


def _percentage_change(current: float, baseline: float) -> str:
    if baseline == 0:
        return "0%"
    change = ((current - baseline) / baseline) * 100
    return f"{change:+.0f}%"


def _not_enough_data_payload() -> dict[str, str]:
    return {
        "fluency": "Not enough data yet",
        "vocabulary": "Not enough data yet",
        "grammar": "Not enough data yet",
        "fillers": "Not enough data yet",
        "pauses": "Not enough data yet",
    }


def _build_trend(db: Session, user_id: str, period: str) -> list[dict]:
    """Build trend data combining practice and roleplay sessions."""
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if period == "month":
        day_count = 30
    elif period == "all":
        first_practice = (
            db.query(PracticeSession)
            .filter(PracticeSession.user_id == user_id)
            .order_by(PracticeSession.created_at.asc())
            .first()
        )
        first_roleplay = (
            db.query(RoleplaySession)
            .filter(RoleplaySession.user_id == user_id)
            .order_by(RoleplaySession.created_at.asc())
            .first()
        )
        
        first_dates = []
        if first_practice:
            first_dates.append(first_practice.created_at.date())
        if first_roleplay:
            first_dates.append(first_roleplay.created_at.date())
        
        if not first_dates:
            day_count = 7
        else:
            day_count = max(1, (today - min(first_dates)).days + 1)
    else:
        day_count = 7

    trend = []
    for offset in range(day_count - 1, -1, -1):
        day = today - timedelta(days=offset)
        
        practice_sessions = (
            db.query(PracticeSession)
            .filter(
                and_(
                    PracticeSession.user_id == user_id,
                    func.date(PracticeSession.created_at) == day,
                )
            )
            .all()
        )
        
        roleplay_sessions = (
            db.query(RoleplaySession)
            .filter(
                and_(
                    RoleplaySession.user_id == user_id,
                    func.date(RoleplaySession.created_at) == day,
                    RoleplaySession.completed_at.isnot(None),
                )
            )
            .all()
        )
        
        # Combine fluency scores from both types
        all_fluency_scores = []
        for s in practice_sessions:
            all_fluency_scores.append(s.fluency_score)
        for s in roleplay_sessions:
            if s.fluency_score is not None:
                all_fluency_scores.append(s.fluency_score)
        
        avg_fluency = sum(all_fluency_scores) / len(all_fluency_scores) if all_fluency_scores else 0
        
        trend.append(
            {
                "date": day.isoformat(),
                "avg_fluency": round(avg_fluency, 1),
                "session_count": len(practice_sessions) + len(roleplay_sessions),
            }
        )
    return trend


def get_progress(db: Session, user: User, period: str = "week") -> dict:
    """Get progress combining both practice and roleplay sessions."""
    period = period if period in {"week", "month", "all"} else "week"
    start, end = _period_range(period)

    # Get practice sessions
    practice_sessions = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.user_id == user.id,
            PracticeSession.created_at >= start,
            PracticeSession.created_at <= end,
        )
        .all()
    )
    
    # Get completed roleplay sessions
    roleplay_sessions = (
        db.query(RoleplaySession)
        .filter(
            RoleplaySession.user_id == user.id,
            RoleplaySession.created_at >= start,
            RoleplaySession.created_at <= end,
            RoleplaySession.completed_at.isnot(None),
        )
        .all()
    )

    # Combine sessions for metrics
    all_sessions = []
    for s in practice_sessions:
        all_sessions.append({
            "fluency_score": s.fluency_score,
            "vocabulary_score": s.vocabulary_score,
            "grammar_score": s.grammar_score,
            "fillers": s.fillers,
            "pauses": s.pauses,
        })
    for s in roleplay_sessions:
        if s.fluency_score is not None:
            all_sessions.append({
                "fluency_score": s.fluency_score,
                "vocabulary_score": s.vocabulary_score,
                "grammar_score": s.grammar_score,
                "fillers": 0,  # Roleplay doesn't track these at session level
                "pauses": 0,
            })

    # For "all" period, don't calculate baseline (would cause overflow)
    # Instead, compare against first session
    if period == "all":
        baseline_sessions = []
    else:
        current_window_days = 7 if period == "week" else 30
        baseline_start = start - timedelta(days=current_window_days)
        
        baseline_practice = (
            db.query(PracticeSession)
            .filter(
                PracticeSession.user_id == user.id,
                PracticeSession.created_at >= baseline_start,
                PracticeSession.created_at < start,
            )
            .all()
        )
        
        baseline_roleplay = (
            db.query(RoleplaySession)
            .filter(
                RoleplaySession.user_id == user.id,
                RoleplaySession.created_at >= baseline_start,
                RoleplaySession.created_at < start,
                RoleplaySession.completed_at.isnot(None),
            )
            .all()
        )
        
        baseline_sessions = []
        for s in baseline_practice:
            baseline_sessions.append({
                "fluency_score": s.fluency_score,
                "vocabulary_score": s.vocabulary_score,
                "grammar_score": s.grammar_score,
                "fillers": s.fillers,
                "pauses": s.pauses,
            })
        for s in baseline_roleplay:
            if s.fluency_score is not None:
                baseline_sessions.append({
                    "fluency_score": s.fluency_score,
                    "vocabulary_score": s.vocabulary_score,
                    "grammar_score": s.grammar_score,
                    "fillers": 0,
                    "pauses": 0,
                })

    baseline = "previous_week" if baseline_sessions else "first_session"

    def _avg_dict(sessions: list[dict], field: str) -> float:
        if not sessions:
            return 0.0
        return sum(s[field] for s in sessions) / len(sessions)

    if not baseline_sessions and len(all_sessions) < 2:
        improvements = _not_enough_data_payload()
        baseline = "first_session"
    elif not baseline_sessions:
        # Compare to first session
        first_practice = (
            db.query(PracticeSession)
            .filter(PracticeSession.user_id == user.id)
            .order_by(PracticeSession.created_at.asc())
            .first()
        )
        first_roleplay = (
            db.query(RoleplaySession)
            .filter(RoleplaySession.user_id == user.id, RoleplaySession.completed_at.isnot(None))
            .order_by(RoleplaySession.created_at.asc())
            .first()
        )
        
        baseline_sessions = []
        if first_practice:
            baseline_sessions.append({
                "fluency_score": first_practice.fluency_score,
                "vocabulary_score": first_practice.vocabulary_score,
                "grammar_score": first_practice.grammar_score,
                "fillers": first_practice.fillers,
                "pauses": first_practice.pauses,
            })
        elif first_roleplay and first_roleplay.fluency_score is not None:
            baseline_sessions.append({
                "fluency_score": first_roleplay.fluency_score,
                "vocabulary_score": first_roleplay.vocabulary_score,
                "grammar_score": first_roleplay.grammar_score,
                "fillers": 0,
                "pauses": 0,
            })
        
        if baseline_sessions:
            improvements = {
                "fluency": _percentage_change(_avg_dict(all_sessions, "fluency_score"), _avg_dict(baseline_sessions, "fluency_score")),
                "vocabulary": _percentage_change(_avg_dict(all_sessions, "vocabulary_score"), _avg_dict(baseline_sessions, "vocabulary_score")),
                "grammar": _percentage_change(_avg_dict(all_sessions, "grammar_score"), _avg_dict(baseline_sessions, "grammar_score")),
                "fillers": _percentage_change(_avg_dict(all_sessions, "fillers"), _avg_dict(baseline_sessions, "fillers")),
                "pauses": _percentage_change(_avg_dict(all_sessions, "pauses"), _avg_dict(baseline_sessions, "pauses")),
            }
        else:
            improvements = _not_enough_data_payload()
    else:
        improvements = {
            "fluency": _percentage_change(_avg_dict(all_sessions, "fluency_score"), _avg_dict(baseline_sessions, "fluency_score")),
            "vocabulary": _percentage_change(_avg_dict(all_sessions, "vocabulary_score"), _avg_dict(baseline_sessions, "vocabulary_score")),
            "grammar": _percentage_change(_avg_dict(all_sessions, "grammar_score"), _avg_dict(baseline_sessions, "grammar_score")),
            "fillers": _percentage_change(_avg_dict(all_sessions, "fillers"), _avg_dict(baseline_sessions, "fillers")),
            "pauses": _percentage_change(_avg_dict(all_sessions, "pauses"), _avg_dict(baseline_sessions, "pauses")),
        }

    streak = calculate_streak(db, user.id)
    trend = _build_trend(db, user.id, period)

    prompts_completed = (
        db.query(PracticeSession.prompt_id)
        .filter(PracticeSession.user_id == user.id, PracticeSession.attempt_number == 1)
        .distinct()
        .count()
    )

    completed_ids_current_level = {
        row[0]
        for row in db.query(PracticeSession.prompt_id)
        .join(Prompt, PracticeSession.prompt_id == Prompt.id)
        .filter(PracticeSession.user_id == user.id, Prompt.level == user.level, PracticeSession.attempt_number == 1)
        .all()
    }
    total_prompts_level = db.query(Prompt).filter(Prompt.level == user.level).count()
    prompts_remaining = max(0, total_prompts_level - len(completed_ids_current_level))

    return {
        "streak": streak,
        "total_sessions": len(all_sessions),
        "weekly_trend": trend,
        "improvements": improvements,
        "baseline": baseline,
        "level": user.level.value,
        "prompts_completed": prompts_completed,
        "prompts_remaining_in_level": prompts_remaining,
    }

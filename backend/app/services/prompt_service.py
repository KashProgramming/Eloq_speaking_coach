import random
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Prompt, Session as PracticeSession, User, UserLevel


def level_up(level: UserLevel) -> UserLevel:
    if level == UserLevel.beginner:
        return UserLevel.intermediate
    if level == UserLevel.intermediate:
        return UserLevel.advanced
    return UserLevel.advanced


def get_daily_prompt(db: Session, user: User) -> Prompt:
    """
    Get the daily prompt for a user.
    - If the user already has a prompt for today, return it (allows persistent display)
    - If it's a new day, select a new prompt and update the user's current_daily_prompt
    """
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    
    # If user has a prompt from today, return it (persistent display)
    if user.last_prompt_date and user.last_prompt_date.date() == today and user.current_daily_prompt_id:
        prompt = db.query(Prompt).filter(Prompt.id == user.current_daily_prompt_id).first()
        if prompt:
            return prompt
    
    # It's a new day or first time - select a new prompt
    # Get all completed prompt IDs for this user (only count attempt_number=1 to avoid counting retries)
    completed_prompt_ids = [
        row[0]
        for row in db.execute(
            select(PracticeSession.prompt_id)
            .where(PracticeSession.user_id == user.id, PracticeSession.attempt_number == 1)
        ).all()
    ]

    # Get available prompts at current level that haven't been completed
    query = select(Prompt).where(Prompt.level == user.level)
    if completed_prompt_ids:
        query = query.where(Prompt.id.notin_(completed_prompt_ids))

    available_prompts = db.execute(query).scalars().all()

    # If no available prompts at current level, check if user completed ALL prompts at this level
    if not available_prompts:
        # Count total prompts at current level
        total_prompts_at_level = db.execute(
            select(func.count(Prompt.id)).where(Prompt.level == user.level)
        ).scalar()

        # Count completed prompts at current level
        completed_at_level = db.execute(
            select(func.count(PracticeSession.prompt_id.distinct()))
            .join(Prompt, PracticeSession.prompt_id == Prompt.id)
            .where(
                PracticeSession.user_id == user.id,
                Prompt.level == user.level,
                PracticeSession.attempt_number == 1
            )
        ).scalar()

        # Only level up if user completed ALL prompts at current level
        if completed_at_level >= total_prompts_at_level and total_prompts_at_level > 0:
            next_level = level_up(user.level)
            if next_level != user.level:
                user.level = next_level
                db.commit()
                db.refresh(user)
                # Get prompts from new level
                available_prompts = db.execute(select(Prompt).where(Prompt.level == user.level)).scalars().all()
            else:
                # Already at max level and completed everything
                raise ValueError("Congratulations! You've completed all available prompts at all levels.")
        else:
            # User hasn't completed all prompts at current level, something is wrong
            raise ValueError(f"No prompts available at your current level. Please contact support.")

    if not available_prompts:
        raise ValueError(f"No prompts configured for level '{user.level.value}'")

    # Select a new prompt
    selected_prompt = random.choice(available_prompts)
    
    # Update user's current daily prompt and last_prompt_date
    user.current_daily_prompt_id = selected_prompt.id
    user.last_prompt_date = datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    db.commit()
    db.refresh(user)

    return selected_prompt

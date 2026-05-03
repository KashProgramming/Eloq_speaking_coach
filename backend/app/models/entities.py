import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class PromptCategory(str, enum.Enum):
    opinion = "opinion"
    narration = "narration"
    explanation = "explanation"
    argument = "argument"


class RoleplayScenario(str, enum.Enum):
    interview = "interview"
    debate = "debate"
    pitch = "pitch"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[UserLevel] = mapped_column(
        SAEnum(UserLevel, name="user_level", native_enum=False), default=UserLevel.beginner
    )
    streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_active: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_prompt_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_daily_prompt_id: Mapped[str | None] = mapped_column(String, ForeignKey("prompts.id"), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    roleplay_sessions: Mapped[list["RoleplaySession"]] = relationship(
        "RoleplaySession", back_populates="user", cascade="all, delete-orphan"
    )
    current_daily_prompt: Mapped["Prompt | None"] = relationship("Prompt", foreign_keys=[current_daily_prompt_id])


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[UserLevel] = mapped_column(
        SAEnum(UserLevel, name="prompt_level", native_enum=False), nullable=False, index=True
    )
    category: Mapped[PromptCategory] = mapped_column(
        SAEnum(PromptCategory, name="prompt_category", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="prompt")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_id: Mapped[str] = mapped_column(String, ForeignKey("prompts.id"), nullable=False)

    audio_url: Mapped[str] = mapped_column(String, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)

    wpm: Mapped[float] = mapped_column(Float, nullable=False)
    fillers: Mapped[int] = mapped_column(Integer, nullable=False)
    pauses: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)

    fluency_score: Mapped[int] = mapped_column(Integer, nullable=False)
    vocabulary_score: Mapped[int] = mapped_column(Integer, nullable=False)
    grammar_score: Mapped[int] = mapped_column(Integer, nullable=False)
    structure_score: Mapped[int] = mapped_column(Integer, nullable=False)

    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    grammar_mistakes: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    original_session_id: Mapped[str | None] = mapped_column(String, ForeignKey("sessions.id"), nullable=True)

    ideal_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ideal_answer_audio_url: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)

    user: Mapped[User] = relationship("User", back_populates="sessions")
    prompt: Mapped[Prompt] = relationship("Prompt", back_populates="sessions")
    original_session: Mapped["Session | None"] = relationship(
        "Session", remote_side=[id], back_populates="retries"
    )
    retries: Mapped[list["Session"]] = relationship("Session", back_populates="original_session")


class RoleplaySession(Base):
    __tablename__ = "roleplay_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scenario: Mapped[RoleplayScenario] = mapped_column(
        SAEnum(RoleplayScenario, name="roleplay_scenario", native_enum=False), nullable=False
    )
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    max_turns: Mapped[int] = mapped_column(Integer, default=3)

    conversation_history: Mapped[str] = mapped_column(Text, nullable=False)

    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    areas_to_improve: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Comprehensive metrics (averaged across all turns)
    fluency_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vocabulary_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grammar_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structure_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="roleplay_sessions")
    turn_audio: Mapped[list["RoleplayTurnAudio"]] = relationship(
        "RoleplayTurnAudio", back_populates="session", cascade="all, delete-orphan"
    )
    assistant_audio: Mapped[list["RoleplayAssistantAudio"]] = relationship(
        "RoleplayAssistantAudio", back_populates="session", cascade="all, delete-orphan"
    )
    turn_metrics: Mapped[list["RoleplayTurnMetrics"]] = relationship(
        "RoleplayTurnMetrics", back_populates="session", cascade="all, delete-orphan"
    )


class RoleplayTurnAudio(Base):
    __tablename__ = "roleplay_turn_audio"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("roleplay_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    audio_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    session: Mapped[RoleplaySession] = relationship("RoleplaySession", back_populates="turn_audio")


class RoleplayAssistantAudio(Base):
    __tablename__ = "roleplay_assistant_audio"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("roleplay_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    audio_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    session: Mapped[RoleplaySession] = relationship("RoleplaySession", back_populates="assistant_audio")


class RoleplayTurnMetrics(Base):
    __tablename__ = "roleplay_turn_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("roleplay_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    
    wpm: Mapped[float] = mapped_column(Float, nullable=False)
    fillers: Mapped[int] = mapped_column(Integer, nullable=False)
    pauses: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    fluency_score: Mapped[int] = mapped_column(Integer, nullable=False)
    vocabulary_score: Mapped[int] = mapped_column(Integer, nullable=False)
    grammar_score: Mapped[int] = mapped_column(Integer, nullable=False)
    structure_score: Mapped[int] = mapped_column(Integer, nullable=False)
    
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    session: Mapped[RoleplaySession] = relationship("RoleplaySession", back_populates="turn_metrics")


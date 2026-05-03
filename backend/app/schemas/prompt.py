from datetime import datetime

from pydantic import BaseModel


class PromptResponse(BaseModel):
    prompt_id: str
    level: str
    category: str
    text: str


class PracticeSessionHistoryItem(BaseModel):
    session_id: str
    prompt_text: str
    prompt_category: str
    audio_url: str
    transcript: str
    duration: float
    wpm: float
    fillers: int
    pauses: int
    word_count: int
    fluency_score: int
    vocabulary_score: int
    grammar_score: int
    structure_score: int
    ideal_answer: str | None
    ideal_answer_audio_url: str | None
    feedback: list[str] | None
    grammar_mistakes: list[str] | None
    created_at: datetime


class PracticeHistoryResponse(BaseModel):
    sessions: list[PracticeSessionHistoryItem]
    total: int


# New schemas for grouped history with attempts
class AttemptSummary(BaseModel):
    session_id: str
    attempt_number: int
    created_at: datetime
    fluency_score: int
    vocabulary_score: int
    grammar_score: int
    structure_score: int
    wpm: float
    fillers: int
    pauses: int


class GroupedPracticeSession(BaseModel):
    prompt_text: str
    prompt_category: str
    date: str  # Date string for grouping (YYYY-MM-DD)
    attempts: list[AttemptSummary]


class GroupedPracticeHistoryResponse(BaseModel):
    sessions: list[GroupedPracticeSession]
    total: int

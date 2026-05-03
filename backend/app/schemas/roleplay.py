from datetime import datetime

from pydantic import BaseModel


class RoleplayStartRequest(BaseModel):
    scenario: str


class RoleplayStartResponse(BaseModel):
    session_id: str
    scenario: str
    opening_question: str
    turn_count: int
    max_turns: int
    audio_url: str | None = None


class TurnEvaluation(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    scores: dict[str, int]  # fluency, vocabulary, grammar, structure


class RoleplayOverallSummary(BaseModel):
    strengths: list[str]
    areas_to_improve: list[str]
    overall_score: int
    avg_fluency: int
    avg_vocabulary: int
    avg_grammar: int
    avg_structure: int


class RoleplayRespondResponse(BaseModel):
    transcript: str
    evaluation: TurnEvaluation
    follow_up_question: str | None = None
    follow_up_audio_url: str | None = None
    turn_count: int
    is_final_turn: bool
    overall_summary: RoleplayOverallSummary | None = None


class RoleplayHistoryResponse(BaseModel):
    session_id: str
    scenario: str
    turn_count: int
    max_turns: int
    history: list[dict[str, str]]


class ConversationTurn(BaseModel):
    role: str
    content: str
    audio_url: str | None = None


class RoleplaySessionHistoryItem(BaseModel):
    session_id: str
    scenario: str
    turn_count: int
    max_turns: int
    overall_score: int | None
    strengths: list[str] | None
    areas_to_improve: list[str] | None
    fluency_score: int | None
    vocabulary_score: int | None
    grammar_score: int | None
    structure_score: int | None
    created_at: datetime
    completed_at: datetime | None
    conversation_history: list[ConversationTurn]


class RoleplaySessionsListResponse(BaseModel):
    sessions: list[RoleplaySessionHistoryItem]
    total: int

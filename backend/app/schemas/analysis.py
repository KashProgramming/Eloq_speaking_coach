from pydantic import BaseModel


class MetricsResponse(BaseModel):
    wpm: float
    fillers: int
    pauses: int
    word_count: int


class ScoresResponse(BaseModel):
    fluency: int
    vocabulary: int
    grammar: int
    structure: int


class AnalyzeResponse(BaseModel):
    session_id: str
    audio_url: str
    transcript: str
    duration: float
    metrics: MetricsResponse
    scores: ScoresResponse
    feedback: list[str]
    grammar_mistakes: list[str]


class AttemptSnapshot(BaseModel):
    wpm: float
    fillers: int
    pauses: int
    fluency_score: int


class RetryComparison(BaseModel):
    original_attempt: AttemptSnapshot
    current_attempt: AttemptSnapshot
    improvements: dict[str, str]


class RetryResponse(AnalyzeResponse):
    comparison: RetryComparison


class IdealAnswerResponse(BaseModel):
    ideal_answer: str
    ideal_answer_audio_url: str | None = None

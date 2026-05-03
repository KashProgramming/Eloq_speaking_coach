from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    avg_fluency: float
    session_count: int


class ProgressResponse(BaseModel):
    streak: int
    total_sessions: int
    weekly_trend: list[TrendPoint]
    improvements: dict[str, str]
    baseline: str
    level: str
    prompts_completed: int
    prompts_remaining_in_level: int

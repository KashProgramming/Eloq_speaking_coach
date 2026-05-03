import json
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.config import get_settings

ROLE_MAP = {
    "interview": "interviewer",
    "debate": "debater",
    "pitch": "investor",
}


def _message_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(item.get("text", "") for item in content if isinstance(item, dict)).strip()
    return str(content)


@lru_cache(maxsize=1)
def _get_json_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.3,
        model_kwargs={"response_format": {"type": "json_object"}},
    )


@lru_cache(maxsize=1)
def _get_text_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.3,
    )


def _invoke_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    llm = _get_json_llm()
    parsing_error: Exception | None = None

    for _ in range(2):
        try:
            response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            text = _message_to_text(response.content)
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a JSON object")
            return parsed
        except Exception as exc:  # pragma: no cover - external model behavior
            parsing_error = exc
            continue

    raise ValueError("Malformed JSON returned by LLM") from parsing_error


def _invoke_text(system_prompt: str, user_prompt: str) -> str:
    try:
        llm = _get_text_llm()
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    except Exception as exc:  # pragma: no cover - external model behavior
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from exc
    return _message_to_text(response.content).strip()


def _clamp_score(value: Any, default: int = 7) -> int:
    """Clamp score to 1-10 range. Default is 7 (good baseline)."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    return max(1, min(10, int(round(value))))


def fallback_evaluation() -> dict[str, Any]:
    """Fallback evaluation with reasonable baseline scores."""
    return {
        "scores": {
            "fluency": 7,
            "vocabulary": 7,
            "grammar": 7,
            "structure": 7,
        },
        "feedback": [
            "Your response is understandable. Focus on clearer structure: intro, key points, and conclusion.",
            "Try reducing filler words and pausing briefly before important points.",
            "Practice speaking at a steady pace around 120-150 words per minute.",
        ],
        "grammar_mistakes": [],
    }


def evaluate_speech(
    transcript: str,
    metrics: dict[str, Any],
    prompt_text: str,
    user_level: str,
) -> dict[str, Any]:
    system_prompt = """You are an encouraging public speaking coach who provides constructive, balanced feedback.
Your role is to help learners improve while recognizing their efforts."""
    
    user_prompt = f"""
TRANSCRIPT:
{transcript}

METRICS (already computed):
- Words per minute: {metrics['wpm']}
- Filler words detected: {metrics['fillers']}
- Awkward pauses: {metrics['pauses']}

PROMPT TOPIC:
{prompt_text}

USER LEVEL: {user_level}

Evaluate the speech on these criteria using a 1-10 scale:

SCORING GUIDELINES (be fair and encouraging):
- 9-10: Excellent - Professional quality, minimal issues
- 7-8: Good - Solid performance with minor areas for improvement
- 5-6: Average - Understandable but needs work in several areas
- 3-4: Below Average - Significant issues but shows effort
- 1-2: Poor - Major problems throughout

EVALUATION CRITERIA:

1. FLUENCY (1-10): How smoothly does the speaker communicate?
   - Consider: natural flow, appropriate pacing, minimal awkward pauses
   - Ideal WPM: 120-150 (adjust for user level)
   - Don't penalize heavily for a few fillers if overall flow is good

2. VOCABULARY (1-10): Quality and variety of word choice
   - Consider: appropriate word choice for topic and level
   - Variety and precision of language
   - Don't expect advanced vocabulary from beginner/intermediate users

3. GRAMMAR (1-10): Correctness of language structure
   - Consider: sentence structure, verb tenses, subject-verb agreement
   - Minor mistakes are normal in spoken language
   - Focus on errors that impact clarity

4. STRUCTURE (1-10): Organization and coherence
   - Consider: clear introduction, logical flow, conclusion
   - Relevance to the prompt topic
   - Coherent progression of ideas

IMPORTANT:
- Be ENCOURAGING and FAIR - most attempts deserve 6-8 range
- Only give very low scores (1-4) for truly problematic responses
- Recognize effort and partial success
- Provide 2-4 specific, actionable feedback points
- List specific grammar mistakes only if they impact clarity

Return ONLY valid JSON:
{{
  "scores": {{"fluency": <int>, "vocabulary": <int>, "grammar": <int>, "structure": <int>}},
  "feedback": ["...", "...", "..."],
  "grammar_mistakes": ["..."]
}}
""".strip()

    try:
        result = _invoke_json(system_prompt, user_prompt)
        scores = result.get("scores", {})
        validated = {
            "scores": {
                "fluency": _clamp_score(scores.get("fluency")),
                "vocabulary": _clamp_score(scores.get("vocabulary")),
                "grammar": _clamp_score(scores.get("grammar")),
                "structure": _clamp_score(scores.get("structure")),
            },
            "feedback": result.get("feedback") if isinstance(result.get("feedback"), list) else [],
            "grammar_mistakes": result.get("grammar_mistakes")
            if isinstance(result.get("grammar_mistakes"), list)
            else [],
        }

        if not validated["feedback"]:
            validated["feedback"] = fallback_evaluation()["feedback"]
        return validated
    except ValueError:
        return fallback_evaluation()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - external model behavior
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from exc


def generate_ideal_answer(transcript: str, prompt_text: str, user_level: str) -> str:
    system_prompt = "You are a public speaking coach creating an ideal response."
    user_prompt = f"""
ORIGINAL TRANSCRIPT:
{transcript}

PROMPT TOPIC:
{prompt_text}

USER LEVEL: {user_level}

Rewrite this speech into a polished, fluent version that:
1. Maintains the user's main points and perspective
2. Fixes grammar errors
3. Improves vocabulary appropriate for {user_level}
4. Uses intro -> arguments -> conclusion
5. Uses natural transitions
6. Eliminates filler words

CONSTRAINTS:
- Length: 100-150 words
- Tone: Conversational but polished
- Don't introduce completely new arguments

Return ONLY rewritten speech plain text.
""".strip()

    ideal_answer = _invoke_text(system_prompt, user_prompt)
    if not ideal_answer:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM service unavailable")
    return ideal_answer


def generate_roleplay_opening_question(scenario: str) -> str:
    role = ROLE_MAP[scenario]
    system_prompt = f"""
You are an experienced {role} conducting a realistic {scenario}.
Ask one concise opening question (1-2 sentences).
Respond with plain text only.
""".strip()

    user_prompt = f"SCENARIO: {scenario}\nTURN: 0/3\nAsk your opening question."
    question = _invoke_text(system_prompt, user_prompt)
    return question or "Tell me about yourself and why you are a good fit for this scenario."


def evaluate_roleplay_response(scenario: str, transcript: str, metrics: dict[str, Any], user_level: str) -> dict[str, Any]:
    """Evaluate roleplay response with comprehensive metrics like practice mode."""
    system_prompt = """You are an encouraging communication coach who provides balanced, constructive feedback.
Focus on what the user did well AND specific areas for improvement."""
    
    user_prompt = f"""
Scenario: {scenario}
Response transcript:
{transcript}

METRICS (already computed):
- Words per minute: {metrics['wpm']}
- Filler words detected: {metrics['fillers']}
- Awkward pauses: {metrics['pauses']}

USER LEVEL: {user_level}

Evaluate this roleplay response on these criteria using a 1-10 scale:

SCORING GUIDELINES (be fair and encouraging):
- 9-10: Excellent - Professional quality, minimal issues
- 7-8: Good - Solid performance with minor areas for improvement
- 5-6: Average - Understandable but needs work in several areas
- 3-4: Below Average - Significant issues but shows effort
- 1-2: Poor - Major problems throughout

EVALUATION CRITERIA:

1. FLUENCY (1-10): How smoothly does the speaker communicate?
   - Consider: natural flow, appropriate pacing, minimal awkward pauses
   - Ideal WPM: 120-150 (adjust for user level)
   - Don't penalize heavily for a few fillers if overall flow is good

2. VOCABULARY (1-10): Quality and variety of word choice
   - Consider: appropriate word choice for scenario and level
   - Variety and precision of language
   - Don't expect advanced vocabulary from beginner/intermediate users

3. GRAMMAR (1-10): Correctness of language structure
   - Consider: sentence structure, verb tenses, subject-verb agreement
   - Minor mistakes are normal in spoken language
   - Focus on errors that impact clarity

4. STRUCTURE (1-10): Organization and coherence
   - Consider: clear points, logical flow, relevance to scenario
   - Coherent progression of ideas
   - Appropriate for the roleplay context

STRENGTHS: Identify 2-3 specific things the user did well
- Examples: clear communication, relevant points, good examples, appropriate tone, confidence

WEAKNESSES: Identify 1-2 specific areas for improvement (be constructive, not harsh)
- Examples: could add more detail, consider alternative perspective, improve structure

Be ENCOURAGING and SPECIFIC. Recognize effort and partial success.

Return ONLY JSON:
{{
  "scores": {{"fluency": <int>, "vocabulary": <int>, "grammar": <int>, "structure": <int>}},
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."]
}}
""".strip()

    try:
        result = _invoke_json(system_prompt, user_prompt)
        scores = result.get("scores", {})
        validated = {
            "scores": {
                "fluency": _clamp_score(scores.get("fluency")),
                "vocabulary": _clamp_score(scores.get("vocabulary")),
                "grammar": _clamp_score(scores.get("grammar")),
                "structure": _clamp_score(scores.get("structure")),
            },
            "strengths": result.get("strengths") if isinstance(result.get("strengths"), list) else [],
            "weaknesses": result.get("weaknesses") if isinstance(result.get("weaknesses"), list) else [],
        }
        
        if not validated["strengths"]:
            validated["strengths"] = ["Clear attempt to answer the question"]
        if not validated["weaknesses"]:
            validated["weaknesses"] = ["Add more specific examples"]
        
        return validated
    except ValueError:
        return {
            "scores": {"fluency": 7, "vocabulary": 7, "grammar": 7, "structure": 7},
            "strengths": ["Clear attempt to answer the question"],
            "weaknesses": ["Add more specific examples"],
        }


def generate_roleplay_followup_question(
    scenario: str,
    turn_count: int,
    max_turns: int,
    history: list[dict[str, str]],
    transcript: str,
) -> str:
    role = ROLE_MAP[scenario]
    system_prompt = f"""
You are an experienced {role} conducting a realistic {scenario}.
Ask ONE follow-up question based on the user's previous response.
Keep it challenging but fair and concise.
Respond with plain text only.
""".strip()

    history_text = "\n".join([f"{item['role']}: {item['content']}" for item in history[-8:]])
    user_prompt = f"""
SCENARIO: {scenario}
TURN: {turn_count}/{max_turns}

CONVERSATION SO FAR:
{history_text}

USER'S PREVIOUS RESPONSE:
{transcript}

Ask your next question.
""".strip()

    question = _invoke_text(system_prompt, user_prompt)
    return question or "Can you share a concrete example that supports your previous point?"


def generate_roleplay_final_summary(scenario: str, history: list[dict[str, str]], turn_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate final summary with averaged comprehensive metrics."""
    system_prompt = """You are an encouraging speaking coach providing final roleplay feedback.
Be fair, balanced, and constructive. Recognize effort and progress."""
    
    history_text = "\n".join([f"{item['role']}: {item['content']}" for item in history[-10:]])
    
    # Calculate average scores from turn metrics
    avg_fluency = sum(m["fluency_score"] for m in turn_metrics) / len(turn_metrics) if turn_metrics else 7
    avg_vocabulary = sum(m["vocabulary_score"] for m in turn_metrics) / len(turn_metrics) if turn_metrics else 7
    avg_grammar = sum(m["grammar_score"] for m in turn_metrics) / len(turn_metrics) if turn_metrics else 7
    avg_structure = sum(m["structure_score"] for m in turn_metrics) / len(turn_metrics) if turn_metrics else 7
    
    user_prompt = f"""
Scenario: {scenario}
Conversation:
{history_text}

AVERAGE SCORES ACROSS ALL TURNS:
- Fluency: {avg_fluency:.1f}/10
- Vocabulary: {avg_vocabulary:.1f}/10
- Grammar: {avg_grammar:.1f}/10
- Structure: {avg_structure:.1f}/10

Provide a final evaluation of this roleplay session:

OVERALL SCORE (1-10): Be FAIR and ENCOURAGING
- 9-10: Excellent performance, professional quality
- 7-8: Good performance with minor areas for improvement
- 5-6: Average performance, shows effort but needs work
- 3-4: Below average, significant issues but shows some understanding
- 1-2: Poor performance with major problems

Most genuine attempts should score 6-8. Only give very low scores for truly problematic responses.

STRENGTHS: List 2-3 specific things the user did well throughout the conversation

AREAS TO IMPROVE: List 1-2 specific, actionable improvements (be constructive)

Return ONLY JSON:
{{
  "strengths": ["...", "..."],
  "areas_to_improve": ["...", "..."],
  "overall_score": <int 1-10>
}}
""".strip()

    try:
        result = _invoke_json(system_prompt, user_prompt)
        strengths = result.get("strengths") if isinstance(result.get("strengths"), list) else []
        areas = result.get("areas_to_improve") if isinstance(result.get("areas_to_improve"), list) else []
        score = _clamp_score(result.get("overall_score"), default=7)

        if not strengths:
            strengths = ["Consistent communication"]
        if not areas:
            areas = ["Add more concrete supporting examples"]

        return {
            "strengths": strengths,
            "areas_to_improve": areas,
            "overall_score": score,
            "avg_fluency": int(round(avg_fluency)),
            "avg_vocabulary": int(round(avg_vocabulary)),
            "avg_grammar": int(round(avg_grammar)),
            "avg_structure": int(round(avg_structure)),
        }
    except ValueError:
        return {
            "strengths": ["Consistent communication"],
            "areas_to_improve": ["Add more concrete supporting examples"],
            "overall_score": 7,
            "avg_fluency": int(round(avg_fluency)),
            "avg_vocabulary": int(round(avg_vocabulary)),
            "avg_grammar": int(round(avg_grammar)),
            "avg_structure": int(round(avg_structure)),
        }

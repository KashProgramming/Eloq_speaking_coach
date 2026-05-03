FILLER_WORDS = [
    "um",
    "uh",
    "like",
    "you know",
    "sort of",
    "kind of",
    "actually",
    "basically",
    "literally",
]

PAUSE_THRESHOLD_SEC = 0.8


def compute_metrics(transcript: str, duration: float, segments: list[dict]) -> dict:
    words = transcript.split()
    word_count = len(words)
    wpm = (word_count / duration) * 60 if duration > 0 else 0

    transcript_lower = transcript.lower()
    fillers = sum(transcript_lower.count(filler) for filler in FILLER_WORDS)

    pauses = 0
    for i in range(len(segments) - 1):
        gap = segments[i + 1]["start"] - segments[i]["end"]
        if gap > PAUSE_THRESHOLD_SEC:
            pauses += 1

    return {
        "wpm": round(wpm, 1),
        "fillers": fillers,
        "pauses": pauses,
        "word_count": word_count,
        "duration": round(duration, 1),
    }

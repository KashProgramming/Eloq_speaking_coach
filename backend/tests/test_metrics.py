from app.services.metrics_service import compute_metrics


def test_compute_metrics_basic():
    transcript = "um I think this is basically a good example"
    duration = 30.0
    segments = [
        {"start": 0.0, "end": 3.0, "text": "um I think"},
        {"start": 4.2, "end": 7.0, "text": "this is"},
        {"start": 8.4, "end": 10.0, "text": "basically a good example"},
    ]

    metrics = compute_metrics(transcript, duration, segments)
    assert metrics["word_count"] == 9
    assert metrics["wpm"] == 18.0
    assert metrics["fillers"] >= 2
    assert metrics["pauses"] == 2

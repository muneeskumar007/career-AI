from app.services.speech.speech_analyzer import (
    WordTimestamp,
    analyze_speech,
    compute_pronunciation_proxy_score,
    compute_speaking_confidence_score,
    compute_speaking_speed,
    detect_filler_words,
    detect_pauses,
)


def _make_words(words, start=0.0, gap=0.3, word_duration=0.3, confidence=0.95):
    """Builds a synthetic word-timestamp sequence with even spacing, useful
    as a baseline 'clean speech' fixture for tests to modify from."""
    timestamps = []
    t = start
    for word in words:
        timestamps.append(WordTimestamp(word=word, start=t, end=t + word_duration, confidence=confidence))
        t += word_duration + gap
    return timestamps


def test_speaking_speed_computed_correctly():
    # 150 words in 60 seconds = 150 WPM
    transcript = " ".join(["word"] * 150)
    assert compute_speaking_speed(transcript, duration_seconds=60) == 150.0


def test_speaking_speed_zero_duration_does_not_crash():
    assert compute_speaking_speed("some words here", duration_seconds=0) == 0.0


def test_filler_word_detection_counts_single_tokens():
    transcript = "So, um, I think, uh, this is like a good approach, um."
    result = detect_filler_words(transcript)
    assert result["counts"]["um"] == 2
    assert result["counts"]["uh"] == 1
    assert result["counts"]["like"] == 1
    assert result["total"] == 4


def test_filler_word_detection_counts_multiword_phrases():
    transcript = "You know, it was kind of difficult, you know, to sort of finish it."
    result = detect_filler_words(transcript)
    assert result["counts"]["you know"] == 2
    assert result["counts"]["kind of"] == 1
    assert result["counts"]["sort of"] == 1


def test_filler_word_detection_does_not_false_positive_on_substrings():
    # "so" and "actually" as filler risk false-positiving inside other words —
    # verify word-boundary matching, not substring matching
    transcript = "Sonic actuality is not a real word but sounds close to fillers."
    result = detect_filler_words(transcript)
    assert "so" not in result["counts"] or result["counts"].get("so", 0) == 0
    assert result["counts"].get("actually", 0) == 0


def test_filler_rate_normalized_per_100_words():
    transcript = " ".join(["um"] * 5 + ["word"] * 95)  # 5 fillers in 100 words
    result = detect_filler_words(transcript)
    assert result["rate_per_100_words"] == 5.0


def test_no_pauses_in_continuous_speech():
    words = _make_words(["this", "is", "continuous", "speech"], gap=0.2)
    result = detect_pauses(words)
    assert result["count"] == 0
    assert result["total_pause_seconds"] == 0.0


def test_detects_long_pause_between_words():
    words = [
        WordTimestamp(word="hello", start=0.0, end=0.5, confidence=0.9),
        WordTimestamp(word="world", start=3.0, end=3.5, confidence=0.9),  # 2.5s gap — a real pause
    ]
    result = detect_pauses(words)
    assert result["count"] == 1
    assert result["longest_pause_seconds"] == 2.5


def test_short_gaps_not_counted_as_pauses():
    words = [
        WordTimestamp(word="hello", start=0.0, end=0.5, confidence=0.9),
        WordTimestamp(word="world", start=0.9, end=1.4, confidence=0.9),  # 0.4s gap — just normal speech
    ]
    result = detect_pauses(words)
    assert result["count"] == 0


def test_pronunciation_proxy_averages_word_confidence():
    words = _make_words(["clear", "speech", "here"], confidence=0.9)
    score = compute_pronunciation_proxy_score(words)
    assert score == 90.0


def test_pronunciation_proxy_none_when_no_words():
    assert compute_pronunciation_proxy_score([]) is None


def test_confidence_score_penalizes_too_fast_speech():
    normal = compute_speaking_confidence_score(speaking_speed_wpm=140, filler_rate_per_100=0, pause_info={"count": 0}, total_words=100)
    too_fast = compute_speaking_confidence_score(speaking_speed_wpm=220, filler_rate_per_100=0, pause_info={"count": 0}, total_words=100)
    assert too_fast < normal


def test_confidence_score_penalizes_too_slow_speech():
    normal = compute_speaking_confidence_score(speaking_speed_wpm=140, filler_rate_per_100=0, pause_info={"count": 0}, total_words=100)
    too_slow = compute_speaking_confidence_score(speaking_speed_wpm=60, filler_rate_per_100=0, pause_info={"count": 0}, total_words=100)
    assert too_slow < normal


def test_confidence_score_penalizes_filler_words():
    clean = compute_speaking_confidence_score(speaking_speed_wpm=140, filler_rate_per_100=0, pause_info={"count": 0}, total_words=100)
    filler_heavy = compute_speaking_confidence_score(speaking_speed_wpm=140, filler_rate_per_100=10, pause_info={"count": 0}, total_words=100)
    assert filler_heavy < clean


def test_confidence_score_never_goes_below_zero():
    score = compute_speaking_confidence_score(speaking_speed_wpm=400, filler_rate_per_100=50, pause_info={"count": 20}, total_words=50)
    assert score >= 0.0


def test_confidence_score_never_exceeds_100():
    score = compute_speaking_confidence_score(speaking_speed_wpm=140, filler_rate_per_100=0, pause_info={"count": 0}, total_words=1000)
    assert score <= 100.0


def test_full_analysis_pipeline_on_clean_speech():
    words = _make_words(
        "I think this approach demonstrates strong technical judgment and clear communication".split(),
        gap=0.15, confidence=0.95,
    )
    transcript = " ".join(w.word for w in words)
    duration = words[-1].end

    result = analyze_speech(transcript, duration, words)
    assert result["speaking_speed_wpm"] > 0
    assert result["filler_words"]["total"] == 0
    assert result["pauses"]["count"] == 0
    assert result["pronunciation_proxy_score"] == 95.0
    assert result["confidence_score"] > 70
    assert result["communication_score"] > 70


def test_full_analysis_pipeline_on_hesitant_speech():
    transcript = "um so I think uh this is like kind of a good approach you know"
    words = _make_words(transcript.split(), gap=2.0, confidence=0.6)  # long gaps = lots of pauses
    duration = words[-1].end

    result = analyze_speech(transcript, duration, words)
    assert result["filler_words"]["total"] >= 4
    assert result["pauses"]["count"] > 0
    assert result["confidence_score"] < 70

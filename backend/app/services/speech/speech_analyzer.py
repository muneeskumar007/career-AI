"""
Speech analysis logic. Deliberately takes structured, already-transcribed
input (transcript text + word-level timestamps) rather than raw audio —
that separation is what makes this module unit-testable with synthetic data
even though this build environment can't run Whisper itself (see
transcription.py). Every function here is a pure function: same input,
same output, no I/O — the only place real audio actually gets consumed is
transcription.py, which produces the WordTimestamp list this operates on.
"""

import re
from dataclasses import dataclass

FILLER_WORDS = {
    "um", "uh", "uhh", "umm", "erm", "er", "like", "you know", "sort of",
    "kind of", "basically", "actually", "literally", "i mean", "so yeah",
}
# Multi-word fillers need phrase matching, not just token matching
FILLER_PHRASES = [f for f in FILLER_WORDS if " " in f]
FILLER_TOKENS = {f for f in FILLER_WORDS if " " not in f}

PAUSE_THRESHOLD_SECONDS = 1.5

IDEAL_WPM_RANGE = (120, 160)  # typical comfortable conversational speaking pace


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    confidence: float = 1.0  # ASR confidence for this word, 0-1; see transcription.py


def compute_speaking_speed(transcript: str, duration_seconds: float) -> float:
    if duration_seconds <= 0:
        return 0.0
    word_count = len(transcript.split())
    return round(word_count / (duration_seconds / 60), 1)


def detect_filler_words(transcript: str) -> dict:
    text_lower = transcript.lower()
    counts: dict[str, int] = {}

    for phrase in FILLER_PHRASES:
        count = len(re.findall(rf"\b{re.escape(phrase)}\b", text_lower))
        if count:
            counts[phrase] = count

    tokens = re.findall(r"\b[a-z']+\b", text_lower)
    for token in tokens:
        if token in FILLER_TOKENS:
            counts[token] = counts.get(token, 0) + 1

    total_words = max(len(transcript.split()), 1)
    total_fillers = sum(counts.values())
    return {
        "counts": counts,
        "total": total_fillers,
        "rate_per_100_words": round(total_fillers / total_words * 100, 1),
    }


def detect_pauses(word_timestamps: list[WordTimestamp]) -> dict:
    if len(word_timestamps) < 2:
        return {"count": 0, "total_pause_seconds": 0.0, "longest_pause_seconds": 0.0}

    pauses = []
    for prev, curr in zip(word_timestamps, word_timestamps[1:]):
        gap = curr.start - prev.end
        if gap >= PAUSE_THRESHOLD_SECONDS:
            pauses.append(gap)

    return {
        "count": len(pauses),
        "total_pause_seconds": round(sum(pauses), 1),
        "longest_pause_seconds": round(max(pauses), 1) if pauses else 0.0,
    }


def compute_pronunciation_proxy_score(word_timestamps: list[WordTimestamp]) -> float | None:
    """NOT a phonetic pronunciation analysis — there's no dedicated
    pronunciation model in this stack. This is a proxy: the ASR's own
    per-word transcription confidence, averaged. Low confidence *correlates*
    with unclear speech but can equally reflect background noise, accent
    bias in the model, or a quiet microphone — report this as a rough
    signal, not a verdict, and say so wherever it's displayed."""
    if not word_timestamps:
        return None
    return round(sum(w.confidence for w in word_timestamps) / len(word_timestamps) * 100, 1)


def compute_speaking_confidence_score(speaking_speed_wpm: float, filler_rate_per_100: float, pause_info: dict, total_words: int) -> float:
    """A distinct concept from the ASR-confidence pronunciation proxy above —
    this estimates how *confident the candidate sounded*, from observable
    delivery patterns (pace, filler-word rate, pause frequency), not from
    facial expression or tone. Purely rule-based, capped 0-100."""
    score = 100.0

    low, high = IDEAL_WPM_RANGE
    if speaking_speed_wpm < low:
        score -= min((low - speaking_speed_wpm) * 0.5, 25)
    elif speaking_speed_wpm > high:
        score -= min((speaking_speed_wpm - high) * 0.4, 25)

    score -= min(filler_rate_per_100 * 3, 30)

    pause_rate = pause_info["count"] / max(total_words / 100, 1)
    score -= min(pause_rate * 5, 20)

    return round(max(0.0, min(100.0, score)), 1)


def analyze_speech(transcript: str, duration_seconds: float, word_timestamps: list[WordTimestamp]) -> dict:
    speaking_speed = compute_speaking_speed(transcript, duration_seconds)
    fillers = detect_filler_words(transcript)
    pauses = detect_pauses(word_timestamps)
    pronunciation_proxy = compute_pronunciation_proxy_score(word_timestamps)
    total_words = max(len(transcript.split()), 1)
    confidence = compute_speaking_confidence_score(speaking_speed, fillers["rate_per_100_words"], pauses, total_words)

    # Communication score: confidence-in-delivery weighted highest, filler-word
    # cleanliness and pronunciation-proxy as supporting signals.
    components = [confidence, max(0, 100 - fillers["rate_per_100_words"] * 4)]
    if pronunciation_proxy is not None:
        components.append(pronunciation_proxy)
    communication_score = round(sum(components) / len(components), 1)

    return {
        "speaking_speed_wpm": speaking_speed,
        "filler_words": fillers,
        "pauses": pauses,
        "pronunciation_proxy_score": pronunciation_proxy,
        "confidence_score": confidence,
        "communication_score": communication_score,
    }

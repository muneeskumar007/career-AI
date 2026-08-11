"""
Whisper-based audio transcription. NOT LIVE-TESTED in this build: openai-
whisper depends on torch, whose default PyPI wheel pulls ~3GB of CUDA
libraries even for CPU inference (this environment can't reach
download.pytorch.org's CPU-only index, and doesn't have 3GB+ to spare for
libraries it won't use anyway — verified by twice attempting the install and
running out of disk both times, not assumed). The code below follows
openai-whisper's documented API; verify it against the installed version
before relying on it, in an environment that can actually install the
package.

Deliberately isolated from speech_analyzer.py: this is the only function
that touches raw audio and an ML model. Everything downstream operates on
the plain (transcript, duration, word_timestamps) it produces, which is why
that part of Module 9 IS tested here despite this part not being.
"""

import logging

from app.services.speech.speech_analyzer import WordTimestamp
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

_model = None  # loaded once per process, same pattern as spaCy's _get_nlp()


class TranscriptionError(AppException):
    status_code = 502
    message = "Couldn't transcribe this audio. Please try again or check the file format."


def _get_model():
    global _model
    if _model is None:
        import whisper  # deferred import: only needed if this code path actually runs

        _model = whisper.load_model("base")
    return _model


def transcribe_audio(audio_path: str) -> tuple[str, float, list[WordTimestamp]]:
    """Returns (transcript_text, duration_seconds, word_timestamps)."""
    try:
        model = _get_model()
        result = model.transcribe(audio_path, word_timestamps=True)
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        raise TranscriptionError() from exc

    transcript = result["text"].strip()
    duration = result["segments"][-1]["end"] if result.get("segments") else 0.0

    word_timestamps = []
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            word_timestamps.append(
                WordTimestamp(
                    word=word_info["word"].strip(),
                    start=word_info["start"],
                    end=word_info["end"],
                    # Whisper reports per-word probability as "probability" when
                    # word_timestamps=True; fall back to 1.0 if a given build
                    # doesn't surface it, rather than crashing on a KeyError.
                    confidence=word_info.get("probability", 1.0),
                )
            )

    return transcript, duration, word_timestamps

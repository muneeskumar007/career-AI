import { useEffect, useRef, useState } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Video, Send, CheckCircle2, AlertCircle, RotateCcw, ArrowRight } from "lucide-react";
import * as interviewService from "@/services/interviewService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import Loader from "@/components/common/Loader";
import { getApiErrorMessage } from "@/utils/validators";

const CATEGORY_LABELS = {
  hr: "HR", technical: "Technical", project: "Project",
  scenario: "Scenario", behavioral: "Behavioral", coding: "Coding",
};

export default function InterviewSession() {
  const { interviewId } = useParams();
  const location = useLocation();
  const mode = location.state?.mode ?? "text";

  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [textAnswer, setTextAnswer] = useState("");
  const [recordingState, setRecordingState] = useState("idle"); // idle | recording | recorded
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastEvaluation, setLastEvaluation] = useState(null);
  const [error, setError] = useState(null);
  const [mediaError, setMediaError] = useState(null);

  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const videoPreviewRef = useRef(null);
  const recordedUrlRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const q = await interviewService.getCurrentQuestion(interviewId);
        setCurrentQuestion(q);
      } catch (err) {
        setError(getApiErrorMessage(err));
      }
    })();

    const stream = streamRef;
    const recordedUrl = recordedUrlRef;
    return () => {
      stream.current?.getTracks().forEach((t) => t.stop());
      if (recordedUrl.current) window.URL.revokeObjectURL(recordedUrl.current);
    };
  }, [interviewId]);

  const startRecording = async () => {
    setMediaError(null);
    try {
      const constraints = mode === "video" ? { audio: true, video: true } : { audio: true };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (mode === "video" && videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream;
      }

      const recorder = new MediaRecorder(stream, { mimeType: mode === "video" ? "video/webm" : "audio/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mode === "video" ? "video/webm" : "audio/webm" });
        setRecordedBlob(blob);
        streamRef.current?.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecordingState("recording");
    } catch (err) {
      setMediaError(
        err.name === "NotAllowedError"
          ? "Permission denied. Allow microphone/camera access in your browser to use this mode."
          : "Couldn't access your microphone/camera. You can switch to text mode instead."
      );
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecordingState("recorded");
  };

  const retakeRecording = () => {
    setRecordedBlob(null);
    setRecordingState("idle");
  };

  const handleSubmit = async () => {
    if (!currentQuestion) return;
    setIsSubmitting(true);
    setError(null);
    try {
      let result;
      if (mode === "text") {
        result = await interviewService.submitAnswer(interviewId, currentQuestion.question, currentQuestion.category, textAnswer);
      } else if (mode === "voice") {
        result = await interviewService.submitAudioAnswer(interviewId, currentQuestion.question, currentQuestion.category, recordedBlob);
      } else {
        result = await interviewService.submitVideoAnswer(interviewId, currentQuestion.question, currentQuestion.category, recordedBlob);
      }
      setLastEvaluation(result);
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't submit your answer. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = async () => {
    setLastEvaluation(null);
    setTextAnswer("");
    setRecordedBlob(null);
    setRecordingState("idle");
    try {
      const q = await interviewService.getCurrentQuestion(interviewId);
      setCurrentQuestion(q);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  if (!currentQuestion && !error) return <Loader />;

  if (currentQuestion?.is_complete) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-4 py-16 text-center">
        <CheckCircle2 className="h-10 w-10 text-signal" />
        <h1 className="font-display text-2xl font-semibold text-ink-text">Interview complete</h1>
        <p className="text-sm text-ink-muted">Your full performance report is ready.</p>
        <Link to={`/report?interview_id=${interviewId}`}>
          <Button>View performance report</Button>
        </Link>
      </div>
    );
  }

  const canSubmit = mode === "text" ? textAnswer.trim().length > 0 : recordingState === "recorded" && !!recordedBlob;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      {currentQuestion && (
        <div className="flex items-center justify-between text-sm text-ink-muted">
          <span>Question {currentQuestion.question_number} of 8</span>
          <span className="rounded-full bg-signal-dim px-2.5 py-1 text-xs font-medium text-signal">
            {CATEGORY_LABELS[currentQuestion.category] ?? currentQuestion.category}
          </span>
        </div>
      )}

      <Card>
        <p className="font-display text-lg font-medium text-ink-text">{currentQuestion?.question}</p>
      </Card>

      <AnimatePresence mode="wait">
        {!lastEvaluation ? (
          <motion.div key="answer-input" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-4">
            {mode === "text" && (
              <textarea
                rows={6}
                value={textAnswer}
                onChange={(e) => setTextAnswer(e.target.value)}
                placeholder="Type your answer…"
                className="w-full resize-y rounded-xl border border-hairline bg-surface/60 p-3.5 text-sm text-ink-text placeholder:text-ink-muted outline-none transition-colors focus:border-signal"
              />
            )}

            {mode !== "text" && (
              <Card className="flex flex-col items-center gap-4 py-8">
                {mode === "video" && (
                  <video ref={videoPreviewRef} autoPlay muted playsInline className="aspect-video w-full max-w-sm rounded-xl bg-black" />
                )}

                {recordingState === "idle" && (
                  <Button onClick={startRecording}>
                    {mode === "voice" ? <Mic className="h-4 w-4" /> : <Video className="h-4 w-4" />} Start recording
                  </Button>
                )}
                {recordingState === "recording" && (
                  <Button onClick={stopRecording} variant="secondary">
                    <Square className="h-4 w-4" /> Stop recording
                  </Button>
                )}
                {recordingState === "recorded" && (
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 text-sm text-signal">
                      <CheckCircle2 className="h-4 w-4" /> Recorded
                    </span>
                    <button type="button" onClick={retakeRecording} className="flex items-center gap-1 text-sm text-ink-muted hover:text-signal">
                      <RotateCcw className="h-3.5 w-3.5" /> Retake
                    </button>
                  </div>
                )}

                {mediaError && (
                  <p role="alert" className="flex items-start gap-2 text-center text-sm text-danger">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {mediaError}
                  </p>
                )}
              </Card>
            )}

            {error && (
              <p role="alert" className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
              </p>
            )}

            <Button onClick={handleSubmit} isLoading={isSubmitting} disabled={!canSubmit} fullWidth>
              <Send className="h-4 w-4" /> {isSubmitting ? "Evaluating…" : "Submit answer"}
            </Button>
          </motion.div>
        ) : (
          <motion.div key="evaluation" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
            <Card className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-ink-text">Overall score</p>
                <span className="font-mono-data text-2xl font-semibold text-signal">{lastEvaluation.overall_score}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs text-ink-muted sm:grid-cols-4">
                <div>Technical: <span className="text-ink-text">{lastEvaluation.technical_accuracy}</span></div>
                <div>Completeness: <span className="text-ink-text">{lastEvaluation.completeness}</span></div>
                <div>Communication: <span className="text-ink-text">{lastEvaluation.communication}</span></div>
                <div>Grammar: <span className="text-ink-text">{lastEvaluation.grammar}</span></div>
              </div>
              <p className="border-t border-hairline pt-3 text-sm text-ink-muted">{lastEvaluation.feedback}</p>
            </Card>

            {lastEvaluation.speech_analysis && (
              <Card>
                <p className="mb-2 text-sm font-medium text-ink-text">Speech delivery</p>
                <div className="grid grid-cols-2 gap-2 text-xs text-ink-muted sm:grid-cols-3">
                  <div>Pace: <span className="text-ink-text">{lastEvaluation.speech_analysis.speaking_speed_wpm} WPM</span></div>
                  <div>Filler words: <span className="text-ink-text">{lastEvaluation.speech_analysis.filler_words.total}</span></div>
                  <div>Confidence: <span className="text-ink-text">{lastEvaluation.speech_analysis.confidence_score}</span></div>
                </div>
              </Card>
            )}

            <Button onClick={handleNext} fullWidth>
              <ArrowRight className="h-4 w-4" /> Next question
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

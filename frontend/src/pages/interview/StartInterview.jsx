import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, MessageSquare, Mic, Video, AlertCircle } from "lucide-react";
import * as interviewService from "@/services/interviewService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import { getApiErrorMessage } from "@/utils/validators";

const MODES = [
  { id: "text", label: "Text", icon: MessageSquare, description: "Type your answers. Fastest to practice with." },
  { id: "voice", label: "Voice", icon: Mic, description: "Speak your answers — get feedback on pacing, filler words, and clarity." },
  { id: "video", label: "Video", icon: Video, description: "Full mock interview — adds eye contact, posture, and attention feedback." },
];

export default function StartInterview() {
  const { resumeId } = useParams();
  const [searchParams] = useState(() => new URLSearchParams(window.location.search));
  const jobDescriptionId = searchParams.get("jd") || null;
  const navigate = useNavigate();
  const [mode, setMode] = useState("text");
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    setIsStarting(true);
    setError(null);
    try {
      const result = await interviewService.startInterview(resumeId, jobDescriptionId, mode);
      navigate(`/interview/${result.interview_id}`, { state: { mode } });
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't start the interview. Please try again."));
      setIsStarting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Link to={`/resume/${resumeId}`} className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to resume
      </Link>

      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-text">Start a mock interview</h1>
        <p className="mt-1 text-sm text-ink-muted">Pick how you want to practice.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {MODES.map(({ id, label, icon: Icon, description }) => (
          <motion.button
            key={id}
            type="button"
            onClick={() => setMode(id)}
            whileTap={{ scale: 0.98 }}
            className="text-left"
          >
            <Card className={`flex h-full flex-col gap-3 transition-colors ${mode === id ? "border-signal" : "hover:border-signal/50"}`}>
              <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${mode === id ? "bg-signal text-ink" : "bg-signal-dim text-signal"}`}>
                <Icon className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-medium text-ink-text">{label}</p>
                <p className="mt-1 text-xs text-ink-muted">{description}</p>
              </div>
            </Card>
          </motion.button>
        ))}
      </div>

      {error && (
        <p role="alert" className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
        </p>
      )}

      <Button onClick={handleStart} isLoading={isStarting} fullWidth>
        {isStarting ? "Starting…" : `Start ${mode} interview`}
      </Button>

      {mode !== "text" && (
        <p className="text-center text-xs text-ink-muted">
          Your browser will ask for {mode === "voice" ? "microphone" : "microphone and camera"} permission.
        </p>
      )}
    </div>
  );
}

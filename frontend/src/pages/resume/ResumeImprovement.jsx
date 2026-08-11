import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Sparkles, ArrowRight } from "lucide-react";
import * as interviewService from "@/services/interviewService";
import Card from "@/components/common/Card";
import Loader from "@/components/common/Loader";
import { getApiErrorMessage } from "@/utils/validators";

export default function ResumeImprovement() {
  const { resumeId } = useParams();
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await interviewService.improveResume(resumeId);
        setResult(data);
      } catch (err) {
        setError(getApiErrorMessage(err, "Couldn't generate improvements right now."));
      } finally {
        setIsLoading(false);
      }
    })();
  }, [resumeId]);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link to={`/resume/${resumeId}`} className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to resume
      </Link>

      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-text">Resume improvements</h1>
        <p className="mt-1 text-sm text-ink-muted">Rewrites your own content for clarity and impact — never invents new experience.</p>
      </div>

      {isLoading && <Loader />}
      {error && <p className="text-sm text-danger">{error}</p>}

      {result && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
          {result.improved_summary && (
            <Card>
              <h2 className="mb-2 text-sm font-medium text-ink-text">Summary</h2>
              <p className="text-sm text-ink-text">{result.improved_summary}</p>
            </Card>
          )}

          {result.improved_experience.map((entry, i) => (
            <Card key={`exp-${i}`} className="flex flex-col gap-3">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">Experience</p>
              <p className="text-sm text-ink-muted line-through decoration-danger/40">{entry.original}</p>
              <div className="flex items-start gap-2">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-signal" />
                <p className="text-sm text-ink-text">{entry.improved}</p>
              </div>
              <p className="text-xs text-ink-muted">{entry.changes}</p>
            </Card>
          ))}

          {result.improved_projects.map((entry, i) => (
            <Card key={`proj-${i}`} className="flex flex-col gap-3">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">Project</p>
              <p className="text-sm text-ink-muted line-through decoration-danger/40">{entry.original}</p>
              <div className="flex items-start gap-2">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-signal" />
                <p className="text-sm text-ink-text">{entry.improved}</p>
              </div>
              <p className="text-xs text-ink-muted">{entry.changes}</p>
            </Card>
          ))}

          {result.general_suggestions.length > 0 && (
            <Card>
              <h2 className="mb-2 flex items-center gap-2 text-sm font-medium text-ink-text">
                <Sparkles className="h-4 w-4 text-signal" /> General suggestions
              </h2>
              <ul className="flex flex-col gap-1.5 text-sm text-ink-muted">
                {result.general_suggestions.map((s, i) => <li key={i}>• {s}</li>)}
              </ul>
            </Card>
          )}
        </motion.div>
      )}
    </div>
  );
}

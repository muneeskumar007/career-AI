import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Plus, Trash2 } from "lucide-react";
import * as resumeService from "@/services/resumeService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import Loader from "@/components/common/Loader";

const STATUS_LABEL = { uploaded: "Uploaded", parsed: "Parsed", failed: "Failed" };

export default function ResumeList() {
  const [resumes, setResumes] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const result = await resumeService.listResumes();
        setResumes(result.items);
      } catch {
        setError("Couldn't load your resumes.");
      }
    })();
  }, []);

  const handleDelete = async (id) => {
    await resumeService.deleteResume(id);
    setResumes((prev) => prev.filter((r) => r.id !== id));
  };

  if (resumes === null && !error) return <Loader />;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-text">Your resumes</h1>
          <p className="mt-1 text-sm text-ink-muted">Upload a resume to get it scored and parsed.</p>
        </div>
        <Link to="/resume/upload">
          <Button>
            <Plus className="h-4 w-4" /> Upload
          </Button>
        </Link>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {resumes && resumes.length === 0 && (
        <Card className="flex flex-col items-center gap-3 py-12 text-center">
          <FileText className="h-8 w-8 text-ink-muted" />
          <p className="text-sm text-ink-muted">No resumes yet.</p>
          <Link to="/resume/upload">
            <Button variant="secondary">Upload your first resume</Button>
          </Link>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {resumes?.map((resume, i) => (
          <motion.div key={resume.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <Link to={`/resume/${resume.id}`} className="flex min-w-0 items-center gap-2">
                  <FileText className="h-4 w-4 shrink-0 text-signal" />
                  <span className="truncate text-sm font-medium text-ink-text hover:text-signal">
                    {resume.original_filename}
                  </span>
                </Link>
                <button
                  type="button"
                  onClick={() => handleDelete(resume.id)}
                  aria-label={`Delete ${resume.original_filename}`}
                  className="shrink-0 text-ink-muted hover:text-danger"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="flex items-center justify-between text-xs text-ink-muted">
                <span className="rounded-full bg-signal-dim px-2 py-0.5 font-mono-data text-signal">
                  {STATUS_LABEL[resume.status]}
                </span>
                <span>{new Date(resume.created_at).toLocaleDateString()}</span>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

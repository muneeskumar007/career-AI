import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { UploadCloud, FileText, X, AlertCircle } from "lucide-react";
import * as resumeService from "@/services/resumeService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import { getApiErrorMessage } from "@/utils/validators";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_SIZE_MB = 10;

export default function UploadResume() {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const validateAndSetFile = useCallback((file) => {
    setError(null);
    if (!file) return;
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is larger than the ${MAX_SIZE_MB}MB limit.`);
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragActive(false);
      validateAndSetFile(e.dataTransfer.files?.[0]);
    },
    [validateAndSetFile]
  );

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError(null);
    try {
      const resume = await resumeService.uploadResume(selectedFile, setProgress);
      navigate(`/resume/${resume.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err, "Upload failed. Please try again."));
      setIsUploading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-text">Upload your resume</h1>
        <p className="mt-1 text-sm text-ink-muted">PDF or DOCX, up to {MAX_SIZE_MB}MB.</p>
      </div>

      <Card>
        {!selectedFile ? (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
              dragActive ? "border-signal bg-signal-dim" : "border-hairline hover:border-signal/60"
            }`}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-signal-dim text-signal">
              <UploadCloud className="h-6 w-6" />
            </span>
            <p className="text-sm font-medium text-ink-text">Drag and drop your resume here</p>
            <p className="text-xs text-ink-muted">or click to browse</p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => validateAndSetFile(e.target.files?.[0])}
            />
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-4">
            <div className="flex items-center justify-between rounded-xl border border-hairline p-4">
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="h-5 w-5 shrink-0 text-signal" />
                <div className="overflow-hidden">
                  <p className="truncate text-sm font-medium text-ink-text">{selectedFile.name}</p>
                  <p className="text-xs text-ink-muted">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              {!isUploading && (
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  aria-label="Remove file"
                  className="text-ink-muted hover:text-danger"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {isUploading && (
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-hairline/60">
                <motion.div
                  className="h-full rounded-full bg-signal"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: "easeOut" }}
                />
              </div>
            )}

            <Button onClick={handleUpload} isLoading={isUploading} fullWidth>
              {isUploading ? "Uploading & extracting text…" : "Upload resume"}
            </Button>
          </motion.div>
        )}

        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            role="alert"
            className="mt-4 flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </motion.p>
        )}
      </Card>
    </div>
  );
}

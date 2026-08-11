import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { Download, TrendingUp, Sparkles, ArrowLeft } from "lucide-react";
import * as reportService from "@/services/reportService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import Loader from "@/components/common/Loader";
import { getApiErrorMessage } from "@/utils/validators";

function buildRadarData(report) {
  const rows = [
    { metric: "Resume", value: report.resume_score },
    { metric: "ATS", value: report.ats_score },
    { metric: "Interview", value: report.interview_score },
    { metric: "Communication", value: report.communication_score },
    { metric: "Technical", value: report.technical_score },
    { metric: "Confidence", value: report.confidence_score },
  ];
  return rows.map((r) => ({ ...r, value: r.value ?? 0 }));
}

export default function PerformanceReport() {
  const [searchParams] = useSearchParams();
  const resumeId = searchParams.get("resume_id");
  const interviewId = searchParams.get("interview_id");

  const [report, setReport] = useState(null);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [reportData, progressData] = await Promise.all([
          reportService.getReport(resumeId, interviewId),
          reportService.getProgressHistory(),
        ]);
        setReport(reportData);
        setProgress(progressData);
      } catch (err) {
        setError(getApiErrorMessage(err, "No report available yet — upload and parse a resume first."));
      }
    })();
  }, [resumeId, interviewId]);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await reportService.downloadReportPdf(resumeId, interviewId);
    } catch {
      setError("Couldn't export the PDF. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  if (!report && !error) return <Loader />;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link to="/dashboard" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to dashboard
      </Link>

      {error && <p className="text-sm text-danger">{error}</p>}

      {report && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h1 className="font-display text-2xl font-semibold text-ink-text">Performance report</h1>
            <Button onClick={handleExport} isLoading={isExporting} variant="secondary">
              <Download className="h-4 w-4" /> {isExporting ? "Exporting…" : "Export PDF"}
            </Button>
          </div>

          <Card>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={buildRadarData(report)}>
                  <PolarGrid stroke="var(--color-hairline)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "var(--color-ink-muted)", fontSize: 10 }} />
                  <Radar dataKey="value" stroke="var(--color-signal)" fill="var(--color-signal)" fillOpacity={0.35} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {[
              ["Resume", report.resume_score], ["ATS", report.ats_score], ["Interview", report.interview_score],
              ["Communication", report.communication_score], ["Technical", report.technical_score], ["Confidence", report.confidence_score],
            ].map(([label, value]) => (
              <Card key={label} className="text-center">
                <p className="font-mono-data text-xl font-semibold text-ink-text">{value ?? "—"}</p>
                <p className="mt-1 text-xs text-ink-muted">{label}</p>
              </Card>
            ))}
          </div>

          {(report.strong_skills.length > 0 || report.weak_skills.length > 0) && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {report.strong_skills.length > 0 && (
                <Card>
                  <h2 className="mb-2 text-sm font-medium text-ink-text">Strong skills</h2>
                  <div className="flex flex-wrap gap-2">
                    {report.strong_skills.map((s) => (
                      <span key={s} className="rounded-full bg-signal-dim px-3 py-1 text-xs font-medium text-signal">{s}</span>
                    ))}
                  </div>
                </Card>
              )}
              {report.weak_skills.length > 0 && (
                <Card>
                  <h2 className="mb-2 text-sm font-medium text-ink-text">Weak skills</h2>
                  <div className="flex flex-wrap gap-2">
                    {report.weak_skills.map((s) => (
                      <span key={s} className="rounded-full bg-danger/10 px-3 py-1 text-xs font-medium text-danger">{s}</span>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}

          {report.recommendations.length > 0 && (
            <Card>
              <h2 className="mb-3 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                <Sparkles className="h-4 w-4 text-signal" /> Recommendations
              </h2>
              <ul className="flex flex-col gap-2 text-sm text-ink-muted">
                {report.recommendations.map((r, i) => <li key={i}>• {r}</li>)}
              </ul>
            </Card>
          )}

          {progress && progress.points.length > 1 && (
            <Card>
              <h2 className="mb-3 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                <TrendingUp className="h-4 w-4 text-signal" /> Progress over time
              </h2>
              <div className="flex flex-col gap-2">
                {progress.points.map((p) => (
                  <div key={p.interview_id} className="flex items-center justify-between text-sm">
                    <span className="text-ink-muted">{new Date(p.date).toLocaleDateString()}</span>
                    <span className="font-mono-data text-ink-text">{p.interview_score ?? "—"}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </motion.div>
      )}
    </div>
  );
}

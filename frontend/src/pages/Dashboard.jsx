import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Target, Mic, TrendingUp, Award, Lock } from "lucide-react";
import * as reportService from "@/services/reportService";
import { useAuth } from "@/hooks/useAuth";
import Card from "@/components/common/Card";
import Loader from "@/components/common/Loader";

export default function Dashboard() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const firstName = user?.name.split(" ")[0];

  useEffect(() => {
    (async () => {
      try {
        const data = await reportService.getDashboard();
        setDashboard(data);
      } catch {
        setDashboard(null);
      }
    })();
  }, []);

  if (!dashboard) return <Loader />;

  return (
    <div className="flex flex-col gap-8">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="font-display text-2xl font-semibold text-ink-text">Welcome, {firstName}.</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {dashboard.practice_count} mock interview{dashboard.practice_count === 1 ? "" : "s"} completed so far.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: FileText, label: "Upload resume", to: "/resume/upload" },
          { icon: Target, label: "Your resumes", to: "/resume" },
          { icon: Mic, label: "Start an interview", to: dashboard.resume_history[0] ? `/interview/start/${dashboard.resume_history[0].id}` : "/resume" },
          { icon: TrendingUp, label: "Performance report", to: "/report" },
        ].map(({ icon: Icon, label, to }, i) => (
          <motion.div key={label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: i * 0.06 }}>
            <Link to={to}>
              <Card className="flex flex-col gap-3 hover:border-signal">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-signal-dim text-signal">
                  <Icon className="h-4 w-4" />
                </span>
                <p className="text-sm font-medium text-ink-text">{label}</p>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {dashboard.recent_interviews.length > 0 && (
        <Card>
          <h2 className="mb-4 font-display text-lg font-semibold text-ink-text">Recent interviews</h2>
          <div className="flex flex-col divide-y divide-hairline">
            {dashboard.recent_interviews.map((interview) => (
              <Link
                key={interview.id}
                to={interview.status === "completed" ? `/report?interview_id=${interview.id}` : `/interview/${interview.id}`}
                className="flex items-center justify-between py-3 first:pt-0 last:pb-0 hover:text-signal"
              >
                <div>
                  <p className="text-sm font-medium text-ink-text">
                    {interview.mode.charAt(0).toUpperCase() + interview.mode.slice(1)} interview
                  </p>
                  <p className="text-xs text-ink-muted">
                    {interview.status === "completed" ? "Completed" : "In progress"} · {new Date(interview.created_at).toLocaleDateString()}
                  </p>
                </div>
                {interview.overall_score !== null && (
                  <span className="font-mono-data text-sm text-signal">{interview.overall_score}</span>
                )}
              </Link>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
          <Award className="h-4 w-4 text-signal" /> Achievements
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {dashboard.achievements.map((a) => (
            <div
              key={a.id}
              className={`flex flex-col gap-1 rounded-xl border p-3 ${a.unlocked ? "border-signal/40 bg-signal-dim" : "border-hairline opacity-50"}`}
            >
              <div className="flex items-center gap-1.5">
                {a.unlocked ? <Award className="h-3.5 w-3.5 text-signal" /> : <Lock className="h-3.5 w-3.5 text-ink-muted" />}
                <p className="text-xs font-medium text-ink-text">{a.label}</p>
              </div>
              <p className="text-[11px] text-ink-muted">{a.description}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

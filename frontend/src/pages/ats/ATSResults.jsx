import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, CheckCircle2, AlertTriangle, Wrench,
  FolderPlus, Award, Briefcase, GraduationCap, Clock,
} from "lucide-react";
import * as atsService from "@/services/atsService";
import Card from "@/components/common/Card";
import Loader from "@/components/common/Loader";
import { getApiErrorMessage } from "@/utils/validators";

const CATEGORY_LABELS = {
  programming_languages: "Programming Languages",
  frameworks: "Frameworks",
  databases: "Databases",
  cloud: "Cloud & DevOps",
  soft_skills: "Soft Skills",
  certifications: "Certifications",
};

const DIFFICULTY_COLOR = {
  Beginner: "text-signal",
  Intermediate: "text-amber",
  Advanced: "text-danger",
};

function ScoreRing({ score, label }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const color = score >= 75 ? "var(--color-signal)" : score >= 50 ? "var(--color-amber)" : "var(--color-danger)";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-32 w-32">
        <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--color-hairline)" strokeWidth="10" />
          <motion.circle
            cx="60" cy="60" r={radius} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference * (1 - score / 100) }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono-data text-2xl font-semibold text-ink-text">{score}</span>
          <span className="text-[10px] text-ink-muted">/ 100</span>
        </div>
      </div>
      <p className="text-xs font-medium text-ink-muted">{label}</p>
    </div>
  );
}

function SkillTagList({ skillsByCategory, tone }) {
  const entries = Object.entries(skillsByCategory).filter(([, list]) => list.length > 0);
  if (entries.length === 0) return <p className="text-sm text-ink-muted">None</p>;
  return (
    <div className="flex flex-col gap-3">
      {entries.map(([category, list]) => (
        <div key={category}>
          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-muted">{CATEGORY_LABELS[category]}</p>
          <div className="flex flex-wrap gap-2">
            {list.map((skill) => (
              <span
                key={skill}
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  tone === "matched" ? "bg-signal-dim text-signal" : "bg-danger/10 text-danger"
                }`}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ATSResults() {
  const { resumeId, jobDescriptionId } = useParams();
  const [ats, setAts] = useState(null);
  const [skillGap, setSkillGap] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [atsResult, gapResult] = await Promise.all([
          atsService.getATSResult(resumeId, jobDescriptionId),
          atsService.getSkillGap(resumeId, jobDescriptionId),
        ]);
        setAts(atsResult);
        setSkillGap(gapResult);
      } catch (err) {
        setError(getApiErrorMessage(err, "Couldn't load these results."));
      }
    })();
  }, [resumeId, jobDescriptionId]);

  if (!ats && !error) return <Loader />;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link to={`/resume/${resumeId}`} className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to resume
      </Link>

      {error && <p className="text-sm text-danger">{error}</p>}

      {ats && (
        <>
          <Card className="flex flex-col items-center gap-6 sm:flex-row sm:justify-around">
            <ScoreRing score={ats.ats_score} label="Overall ATS Score" />
            <ScoreRing score={ats.skill_match_percent} label="Skill Match" />
            <ScoreRing score={ats.semantic_similarity_percent} label="Content Relevance" />
          </Card>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <h2 className="mb-3 flex items-center gap-2 font-display text-base font-semibold text-ink-text">
                <CheckCircle2 className="h-4 w-4 text-signal" /> Strengths
              </h2>
              <ul className="flex flex-col gap-2 text-sm text-ink-muted">
                {ats.strengths.map((s, i) => <li key={i}>• {s}</li>)}
              </ul>
            </Card>
            <Card>
              <h2 className="mb-3 flex items-center gap-2 font-display text-base font-semibold text-ink-text">
                <AlertTriangle className="h-4 w-4 text-amber" /> Weak Areas
              </h2>
              {ats.weak_areas.length === 0 ? (
                <p className="text-sm text-ink-muted">No major gaps in required skills.</p>
              ) : (
                <ul className="flex flex-col gap-2 text-sm text-ink-muted">
                  {ats.weak_areas.map((s, i) => <li key={i}>• {s}</li>)}
                </ul>
              )}
            </Card>
          </div>

          <Card>
            <h2 className="mb-4 font-display text-lg font-semibold text-ink-text">Skills matched</h2>
            <SkillTagList skillsByCategory={ats.matched_skills} tone="matched" />
          </Card>

          <Card>
            <h2 className="mb-4 font-display text-lg font-semibold text-ink-text">Skills missing</h2>
            <SkillTagList skillsByCategory={ats.missing_skills} tone="missing" />
            {ats.missing_keywords.length > 0 && (
              <div className="mt-4 border-t border-hairline pt-4">
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-muted">
                  Other keywords in the JD not found in your resume
                </p>
                <p className="text-sm text-ink-muted">{ats.missing_keywords.join(", ")}</p>
              </div>
            )}
          </Card>

          {(ats.formatting_suggestions.length > 0 || ats.project_suggestions.length > 0 || ats.certification_suggestions.length > 0 || ats.experience_suggestions.length > 0) && (
            <Card>
              <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                <Wrench className="h-4 w-4 text-signal" /> Recommendations
              </h2>
              <div className="flex flex-col gap-4 text-sm text-ink-muted">
                {ats.formatting_suggestions.map((s, i) => (
                  <p key={`f${i}`} className="flex items-start gap-2"><Wrench className="mt-0.5 h-3.5 w-3.5 shrink-0" />{s}</p>
                ))}
                {ats.project_suggestions.map((s, i) => (
                  <p key={`p${i}`} className="flex items-start gap-2"><FolderPlus className="mt-0.5 h-3.5 w-3.5 shrink-0" />{s}</p>
                ))}
                {ats.certification_suggestions.map((s, i) => (
                  <p key={`c${i}`} className="flex items-start gap-2"><Award className="mt-0.5 h-3.5 w-3.5 shrink-0" />{s}</p>
                ))}
                {ats.experience_suggestions.map((s, i) => (
                  <p key={`e${i}`} className="flex items-start gap-2"><Briefcase className="mt-0.5 h-3.5 w-3.5 shrink-0" />{s}</p>
                ))}
              </div>
            </Card>
          )}

          {skillGap && skillGap.missing_skills.length > 0 && (
            <Card>
              <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                <GraduationCap className="h-4 w-4 text-signal" /> Skill gap &amp; learning plan
              </h2>
              <div className="flex flex-col divide-y divide-hairline">
                {skillGap.missing_skills.map((item) => (
                  <div key={item.skill} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-ink-text">{item.skill}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${item.priority === "High" ? "bg-danger/10 text-danger" : "bg-amber/10 text-amber"}`}>
                          {item.priority} priority
                        </span>
                      </div>
                      <p className={`mt-0.5 text-xs ${DIFFICULTY_COLOR[item.difficulty] ?? "text-ink-muted"}`}>
                        {item.difficulty}
                        {item.recommended_resource && (
                          <>
                            {" · "}
                            <a href={item.recommended_resource} target="_blank" rel="noreferrer" className="underline hover:text-signal">
                              Learning resource
                            </a>
                          </>
                        )}
                      </p>
                    </div>
                    <span className="flex items-center gap-1.5 text-xs text-ink-muted">
                      <Clock className="h-3.5 w-3.5" /> {item.estimated_learning_time}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

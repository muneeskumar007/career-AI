import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, GitBranch, Contact, Globe, GraduationCap, Briefcase, FolderKanban, ArrowLeft, Target } from "lucide-react";
import * as resumeService from "@/services/resumeService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import Loader from "@/components/common/Loader";
import { getApiErrorMessage } from "@/utils/validators";

const SKILL_CATEGORY_LABELS = {
  programming_languages: "Programming Languages",
  frameworks: "Frameworks",
  databases: "Databases",
  cloud: "Cloud & DevOps",
  soft_skills: "Soft Skills",
  certifications: "Certifications",
};

function SkillPills({ skills }) {
  const categories = Object.entries(skills).filter(([, list]) => list.length > 0);
  if (categories.length === 0) {
    return <p className="text-sm text-ink-muted">No skills matched from the taxonomy yet.</p>;
  }
  return (
    <div className="flex flex-col gap-4">
      {categories.map(([category, list]) => (
        <div key={category}>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
            {SKILL_CATEGORY_LABELS[category]}
          </p>
          <div className="flex flex-wrap gap-2">
            {list.map((skill) => (
              <span key={skill} className="rounded-full bg-signal-dim px-3 py-1 text-xs font-medium text-signal">
                {skill}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ResumeDetail() {
  const { resumeId } = useParams();
  const [resume, setResume] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const resumeData = await resumeService.getResume(resumeId);
        setResume(resumeData);
        if (resumeData.status === "parsed") {
          const analysisData = await resumeService.getResumeAnalysis(resumeId);
          setAnalysis(analysisData);
        }
      } catch (err) {
        setError(getApiErrorMessage(err, "Couldn't load this resume."));
      }
    })();
  }, [resumeId]);

  const handleParse = async () => {
    setIsParsing(true);
    setError(null);
    try {
      const analysisData = await resumeService.parseResume(resumeId);
      setAnalysis(analysisData);
      setResume((prev) => ({ ...prev, status: "parsed" }));
    } catch (err) {
      setError(getApiErrorMessage(err, "Parsing failed. Please try again."));
    } finally {
      setIsParsing(false);
    }
  };

  if (!resume && !error) return <Loader />;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link to="/resume" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to resumes
      </Link>

      {error && <p className="text-sm text-danger">{error}</p>}

      {resume && (
        <>
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink-text">{resume.basic_info.name ?? resume.original_filename}</h1>
            <p className="mt-1 text-sm text-ink-muted">
              {resume.basic_info.email} {resume.basic_info.phone && `· ${resume.basic_info.phone}`}
            </p>
          </div>

          {!analysis && (
            <Card className="flex flex-col items-center gap-4 py-10 text-center">
              <Sparkles className="h-8 w-8 text-signal" />
              <div>
                <p className="text-sm font-medium text-ink-text">Ready to parse this resume</p>
                <p className="mt-1 text-xs text-ink-muted">
                  Extracts skills, education, experience, projects, and profile links.
                </p>
              </div>
              <Button onClick={handleParse} isLoading={isParsing}>
                {isParsing ? "Parsing…" : "Parse resume"}
              </Button>
            </Card>
          )}

          {analysis && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <Link to={`/resume/${resumeId}/compare`}>
                  <Button fullWidth>
                    <Target className="h-4 w-4" /> Compare to a job
                  </Button>
                </Link>
                <Link to={`/resume/${resumeId}/improve`}>
                  <Button fullWidth variant="secondary">
                    Improve wording
                  </Button>
                </Link>
                <Link to={`/interview/start/${resumeId}`}>
                  <Button fullWidth variant="secondary">
                    Start mock interview
                  </Button>
                </Link>
              </div>

              {(analysis.links.github || analysis.links.linkedin || analysis.links.portfolio) && (
                <div className="flex flex-wrap gap-3">
                  {analysis.links.github && (
                    <a href={analysis.links.github} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
                      <GitBranch className="h-4 w-4" /> GitHub
                    </a>
                  )}
                  {analysis.links.linkedin && (
                    <a href={analysis.links.linkedin} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
                      <Contact className="h-4 w-4" /> LinkedIn
                    </a>
                  )}
                  {analysis.links.portfolio && (
                    <a href={analysis.links.portfolio} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
                      <Globe className="h-4 w-4" /> Portfolio
                    </a>
                  )}
                </div>
              )}

              {analysis.summary && (
                <Card>
                  <p className="text-sm leading-relaxed text-ink-text">{analysis.summary}</p>
                </Card>
              )}

              <Card>
                <h2 className="mb-4 font-display text-lg font-semibold text-ink-text">Skills</h2>
                <SkillPills skills={analysis.skills} />
              </Card>

              {analysis.experience.length > 0 && (
                <Card>
                  <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                    <Briefcase className="h-4 w-4 text-signal" /> Experience
                  </h2>
                  <div className="flex flex-col gap-4">
                    {analysis.experience.map((exp, i) => (
                      <div key={i} className="border-l-2 border-hairline pl-4">
                        <p className="text-sm font-medium text-ink-text">{exp.title ?? "—"}</p>
                        <p className="text-xs text-ink-muted">
                          {exp.company ?? "Unknown company"} {exp.duration && `· ${exp.duration}`}
                        </p>
                        {exp.description && <p className="mt-1.5 whitespace-pre-line text-sm text-ink-muted">{exp.description}</p>}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {analysis.education.length > 0 && (
                <Card>
                  <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                    <GraduationCap className="h-4 w-4 text-signal" /> Education
                  </h2>
                  <div className="flex flex-col gap-4">
                    {analysis.education.map((edu, i) => (
                      <div key={i} className="border-l-2 border-hairline pl-4">
                        <p className="text-sm font-medium text-ink-text">{edu.degree ?? "Degree not detected"}</p>
                        <p className="text-xs text-ink-muted">
                          {edu.institution ?? "Institution not detected"} {edu.duration && `· ${edu.duration}`}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {analysis.projects.length > 0 && (
                <Card>
                  <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-semibold text-ink-text">
                    <FolderKanban className="h-4 w-4 text-signal" /> Projects
                  </h2>
                  <div className="flex flex-col gap-4">
                    {analysis.projects.map((proj, i) => (
                      <div key={i} className="border-l-2 border-hairline pl-4">
                        <p className="text-sm font-medium text-ink-text">{proj.name}</p>
                        {proj.description && <p className="mt-1 text-sm text-ink-muted">{proj.description}</p>}
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}

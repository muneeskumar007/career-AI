"""Turns a ResumeAnalysisResponse into a compact text block for LLM prompts.
Shared by every module that needs "the candidate's background" as context
(question generation, interviews, evaluation) so the format stays consistent
and this doesn't get reimplemented slightly differently in each one."""

from app.schemas.resume_analysis import ResumeAnalysisResponse


def build_resume_context(analysis: ResumeAnalysisResponse) -> str:
    skills_flat = [
        skill
        for category_skills in analysis.skills.model_dump().values()
        for skill in category_skills
    ]
    experience_lines = [
        f"- {e.title or 'Role'} at {e.company or 'a company'} ({e.duration or 'dates unknown'}): {e.description or 'no description'}"
        for e in analysis.experience
    ]
    project_lines = [f"- {p.name}: {p.description or 'no description'}" for p in analysis.projects]

    parts = []
    if analysis.summary:
        parts.append(f"Summary: {analysis.summary}")
    if skills_flat:
        parts.append(f"Skills: {', '.join(skills_flat)}")
    if experience_lines:
        parts.append("Experience:\n" + "\n".join(experience_lines))
    if project_lines:
        parts.append("Projects:\n" + "\n".join(project_lines))

    return "\n\n".join(parts) if parts else "(no resume details available)"

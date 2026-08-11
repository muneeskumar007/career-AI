"""
'Resume Score' is distinct from 'ATS Score' in the report: ATS score needs a
job description to compare against (Module 4); this is a JD-independent
completeness/quality signal — does the resume have the sections and depth a
well-formed resume should have, regardless of which job it's aimed at. Pure
function, rule-based, testable with a plain resume_analysis dict.
"""


def compute_resume_completeness_score(analysis: dict) -> dict:
    checks = []

    has_summary = bool(analysis.get("summary"))
    checks.append(("Has a summary", has_summary, 10))

    experience = analysis.get("experience", [])
    has_experience = len(experience) > 0
    checks.append(("Has work experience listed", has_experience, 20))

    experience_with_descriptions = sum(1 for e in experience if e.get("description"))
    detailed_experience = experience_with_descriptions == len(experience) and len(experience) > 0
    checks.append(("Experience entries have descriptions", detailed_experience, 15))

    has_education = len(analysis.get("education", [])) > 0
    checks.append(("Has education listed", has_education, 10))

    has_projects = len(analysis.get("projects", [])) > 0
    checks.append(("Has projects listed", has_projects, 10))

    skills = analysis.get("skills", {})
    skill_categories_with_content = sum(1 for v in skills.values() if v)
    broad_skills = skill_categories_with_content >= 3
    checks.append(("Skills span 3+ categories (languages, frameworks, etc.)", broad_skills, 15))

    has_certifications = bool(skills.get("certifications"))
    checks.append(("Has certifications", has_certifications, 5))

    links = analysis.get("links", {})
    has_links = bool(links.get("github") or links.get("linkedin") or links.get("portfolio"))
    checks.append(("Has GitHub/LinkedIn/portfolio link", has_links, 15))

    total_score = sum(points for _, passed, points in checks if passed)
    return {
        "score": total_score,
        "checks": [{"label": label, "passed": passed} for label, passed, _ in checks],
    }

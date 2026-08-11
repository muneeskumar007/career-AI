"""
Module 5: presents the same required/preferred skill gap Module 4 computes,
but from a learning-plan angle (priority/difficulty/resources/time) instead
of a scoring angle. Recomputes from the resume analysis + JD text directly
rather than reading Module 4's stored ats_results, so it works even if an
ATS comparison hasn't been run yet — the two modules share the matching
logic (jd_requirements.py) but are independently usable.
"""

from app.ai.skill_metadata import get_skill_metadata
from app.ai.skills_taxonomy import SKILL_CATEGORIES
from app.services.ats.jd_requirements import extract_jd_skills

_PRIORITY_ORDER = {"High": 0, "Medium": 1}


def analyze_skill_gap(resume_skills: dict, jd_text: str) -> dict:
    jd_skills = extract_jd_skills(jd_text)
    required = jd_skills["required"]
    preferred = jd_skills["preferred"]

    known_skills = []
    for category in SKILL_CATEGORIES:
        for skill in resume_skills.get(category, []):
            known_skills.append({"skill": skill, "category": category})

    gap_items = []
    seen = set()
    for category in SKILL_CATEGORIES:
        already_known = set(resume_skills.get(category, []))
        for skill in required.get(category, []):
            if skill in already_known or (category, skill) in seen:
                continue
            seen.add((category, skill))
            meta = get_skill_metadata(skill)
            gap_items.append({
                "skill": skill, "category": category, "priority": "High",
                "difficulty": meta["difficulty"], "recommended_resource": meta["resource"],
                "estimated_learning_time": meta["estimated_time"],
            })
        for skill in preferred.get(category, []):
            if skill in already_known or (category, skill) in seen:
                continue
            seen.add((category, skill))
            meta = get_skill_metadata(skill)
            gap_items.append({
                "skill": skill, "category": category, "priority": "Medium",
                "difficulty": meta["difficulty"], "recommended_resource": meta["resource"],
                "estimated_learning_time": meta["estimated_time"],
            })

    gap_items.sort(key=lambda item: _PRIORITY_ORDER.get(item["priority"], 99))

    return {"known_skills": known_skills, "missing_skills": gap_items}

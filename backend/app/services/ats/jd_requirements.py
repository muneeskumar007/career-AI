"""
Splits a job description into "required" vs "preferred" sections (same
regex-header technique as resume_parser.split_sections) and extracts skills
from each using Module 3's taxonomy matcher, so a JD's "must-have" skills can
be weighted more heavily than its "nice to have" list when scoring a resume.
"""

import re

from app.services.parsing.resume_parser import extract_skills

REQUIRED_HEADERS = r"(requirements?|required skills?|must have|qualifications|what you.ll need|minimum qualifications)"
PREFERRED_HEADERS = r"(preferred|nice to have|bonus( points)?|plus|good to have)"

_REQUIRED_LINE_RE = re.compile(rf"^\s*{REQUIRED_HEADERS}\s*:?\s*$", re.IGNORECASE)
_PREFERRED_LINE_RE = re.compile(rf"^\s*{PREFERRED_HEADERS}\s*:?\s*$", re.IGNORECASE)


def split_requirements(jd_text: str) -> dict[str, str]:
    lines = jd_text.splitlines()
    sections = {"general": [], "required": [], "preferred": []}
    current = "general"

    for line in lines:
        if _REQUIRED_LINE_RE.match(line):
            current = "required"
        elif _PREFERRED_LINE_RE.match(line):
            current = "preferred"
        else:
            sections[current].append(line)

    return {name: "\n".join(lines_).strip() for name, lines_ in sections.items()}


def extract_jd_skills(jd_text: str) -> dict[str, dict[str, list[str]]]:
    """Returns skills found in the 'required' zone (general + required
    headers) and the 'preferred' zone separately. If a JD has no explicit
    required/preferred headers at all, everything counts as required —
    that's the more conservative assumption for scoring."""
    sections = split_requirements(jd_text)
    required_text = sections["general"] + "\n" + sections["required"]
    preferred_text = sections["preferred"]

    return {
        "required": extract_skills(required_text),
        "preferred": extract_skills(preferred_text) if preferred_text.strip() else {},
    }

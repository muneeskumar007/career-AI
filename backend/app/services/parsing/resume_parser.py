"""
Structured extraction from resume text: skills (taxonomy matching), section
detection (regex headers), education/experience/projects (date-range regex
+ spaCy NER as a supplementary signal), and profile links.

This is a heuristic parser, not a state-of-the-art one — real resume parsing
is a genuinely hard, actively-researched NLP problem. What's here is honest,
testable, and good enough to unblock the ATS/skill-gap modules that depend
on it; expect it to do well on conventionally-formatted resumes and less
well on highly creative layouts (multi-column, heavy graphics, tables used
for visual layout rather than data).
"""

import re
from functools import lru_cache

import spacy

from app.ai.skills_taxonomy import SKILL_CATEGORIES

SECTION_HEADERS = {
    "summary": r"(summary|objective|professional summary|about me|profile)",
    "education": r"(education|academic background|academic qualifications)",
    "experience": r"(experience|work experience|professional experience|employment history|work history)",
    "projects": r"(projects|personal projects|academic projects|key projects)",
    "skills": r"(skills|technical skills|core competencies|key skills)",
    "certifications": r"(certifications?|licenses?( and certifications?)?)",
    "achievements": r"(achievements|awards|honors and awards|honours)",
}
_SECTION_LINE_RE = re.compile(
    r"^\s*(" + "|".join(SECTION_HEADERS.values()) + r")\s*:?\s*$", re.IGNORECASE
)

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_DATE_TOKEN = rf"(?:{MONTH}\.?\s+\d{{4}}|\d{{4}})"
DATE_RANGE_RE = re.compile(
    rf"(?P<start>{_DATE_TOKEN})\s*(?:-|–|—|to)\s*(?P<end>{_DATE_TOKEN}|Present|Current)",
    re.IGNORECASE,
)

GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)", re.IGNORECASE)
GENERIC_URL_RE = re.compile(r"https?://[^\s,)]+")

DEGREE_KEYWORDS_RE = re.compile(
    r"\b(Bachelor|Master|B\.?Tech|M\.?Tech|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|"
    r"M\.?B\.?A\.?|Ph\.?D|Associate|Diploma)\b",
    re.IGNORECASE,
)
# Institution names reliably contain one of these words — more precise than
# spaCy's small-model ORG detection, which (verified against a real sample)
# regularly misfires on short text like "Computer Science" or a degree
# abbreviation. Used first; spaCy ORG is the fallback, not the primary signal.
INSTITUTION_KEYWORDS_RE = re.compile(
    r"^.*\b(University|College|Institute|Polytechnic|School of \w+)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


@lru_cache
def _get_nlp():
    # Loaded once per process (spaCy model load is the expensive part —
    # not per-request), matching the same singleton pattern as the Mongo
    # client in database/mongodb.py.
    return spacy.load("en_core_web_sm")


def split_sections(raw_text: str) -> dict[str, str]:
    lines = raw_text.splitlines()
    sections: dict[str, list[str]] = {}
    current = "header"  # anything before the first recognized header
    sections[current] = []

    for line in lines:
        match = _SECTION_LINE_RE.match(line)
        if match:
            matched_text = match.group(1).lower()
            for canonical, pattern in SECTION_HEADERS.items():
                if re.fullmatch(pattern, matched_text, re.IGNORECASE):
                    current = canonical
                    sections.setdefault(current, [])
                    break
        else:
            sections.setdefault(current, []).append(line)

    return {name: "\n".join(content_lines).strip() for name, content_lines in sections.items()}


def extract_skills(raw_text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {category: [] for category in SKILL_CATEGORIES}
    for category, skills in SKILL_CATEGORIES.items():
        for canonical_name, aliases in skills.items():
            candidates = [canonical_name, *aliases]
            for candidate in candidates:
                pattern = r"(?<![A-Za-z0-9])" + re.escape(candidate) + r"(?![A-Za-z0-9])"
                if re.search(pattern, raw_text, re.IGNORECASE):
                    found[category].append(canonical_name)
                    break
    return found


def extract_links(raw_text: str) -> dict[str, str | None]:
    github = GITHUB_RE.search(raw_text)
    linkedin = LINKEDIN_RE.search(raw_text)

    portfolio = None
    for url in GENERIC_URL_RE.findall(raw_text):
        if "github.com" not in url.lower() and "linkedin.com" not in url.lower():
            portfolio = url.rstrip(".,;")
            break

    return {
        "github": f"https://github.com/{github.group(1)}" if github else None,
        "linkedin": f"https://linkedin.com/in/{linkedin.group(1)}" if linkedin else None,
        "portfolio": portfolio,
    }


def extract_education(section_text: str) -> list[dict]:
    if not section_text:
        return []
    nlp = _get_nlp()
    lines = section_text.splitlines()
    non_empty_idx = [i for i, line in enumerate(lines) if line.strip()]
    degree_starts = [i for i in non_empty_idx if DEGREE_KEYWORDS_RE.search(lines[i])]

    if degree_starts:
        # A degree keyword line marks the start of a new entry — everything
        # up to (not including) the next one belongs to it.
        blocks = []
        for idx, start in enumerate(degree_starts):
            end = degree_starts[idx + 1] if idx + 1 < len(degree_starts) else len(lines)
            block_lines = [lines[i] for i in non_empty_idx if start <= i < end]
            blocks.append("\n".join(block_lines))
    else:
        # No degree keyword anywhere — fall back to blank-line-separated
        # blocks, or the whole section as one entry if there's no blank-line
        # structure either. Never fragment down to one entry per line: that
        # splits a single degree/institution/date block into three weak ones.
        blocks = [b for b in re.split(r"\n\s*\n", section_text) if b.strip()] or [section_text]

    entries = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        degree_match = DEGREE_KEYWORDS_RE.search(block)
        date_match = DATE_RANGE_RE.search(block)
        institution_match = INSTITUTION_KEYWORDS_RE.search(block)
        institution = institution_match.group(0).strip() if institution_match else None
        if not institution:
            doc = nlp(block[:500])
            orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
            institution = orgs[0] if orgs else None

        entries.append(
            {
                "degree": degree_match.group(0) if degree_match else None,
                "institution": institution,
                "duration": f"{date_match.group('start')} - {date_match.group('end')}" if date_match else None,
                "raw_text": block,
            }
        )
    return entries


def extract_experience(section_text: str) -> list[dict]:
    if not section_text:
        return []
    nlp = _get_nlp()
    lines = section_text.splitlines()
    non_empty_idx = [i for i, line in enumerate(lines) if line.strip()]
    anchors = [i for i in non_empty_idx if DATE_RANGE_RE.search(lines[i])]

    if not anchors:
        # No dates anywhere in the section — can't segment into entries
        # reliably; return the whole thing as one so nothing is silently lost.
        text = "\n".join(lines[i] for i in non_empty_idx)
        if not text:
            return []
        doc = nlp(text[:500])
        orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        first_line = lines[non_empty_idx[0]].strip() if non_empty_idx else None
        return [{"title": first_line, "company": orgs[0] if orgs else None, "duration": None, "description": text}]

    entries = []
    header_lookback = 2
    for idx, anchor in enumerate(anchors):
        # Header (title, company) is the 1-2 non-empty lines immediately
        # before this entry's date line — but never reaching back past the
        # previous entry's date line, which would steal its description.
        prev_anchor = anchors[idx - 1] if idx > 0 else -1
        header_idx = [i for i in non_empty_idx if prev_anchor < i < anchor][-header_lookback:]
        header_lines = [lines[i].strip() for i in header_idx]

        # Description runs from just after the date line up to the start of
        # the *next* entry's header zone (or end of section for the last one).
        next_anchor = anchors[idx + 1] if idx + 1 < len(anchors) else len(lines)
        next_header_start = anchors[idx + 1] - header_lookback if idx + 1 < len(anchors) else next_anchor
        desc_idx = [i for i in non_empty_idx if anchor < i < max(next_header_start, anchor + 1)]
        description_lines = [lines[i].strip() for i in desc_idx]

        doc = nlp(" ".join(header_lines)[:500])
        orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        date_match = DATE_RANGE_RE.search(lines[anchor])

        entries.append(
            {
                "title": header_lines[0] if header_lines else None,
                "company": header_lines[1] if len(header_lines) > 1 else (orgs[0] if orgs else None),
                "duration": f"{date_match.group('start')} - {date_match.group('end')}" if date_match else None,
                "description": "\n".join(description_lines) if description_lines else None,
            }
        )
    return entries


def extract_projects(section_text: str) -> list[dict]:
    if not section_text:
        return []
    blocks = re.split(r"\n\s*\n", section_text)
    if len(blocks) == 1:
        blocks = [section_text]

    entries = []
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        entries.append({"name": lines[0], "description": "\n".join(lines[1:]) if len(lines) > 1 else None})
    return entries


def parse_resume(raw_text: str) -> dict:
    sections = split_sections(raw_text)
    return {
        "skills": extract_skills(raw_text),
        "links": extract_links(raw_text),
        "education": extract_education(sections.get("education", "")),
        "experience": extract_experience(sections.get("experience", "")),
        "projects": extract_projects(sections.get("projects", "")),
        "summary": sections.get("summary") or None,
    }

"""
The ATS score itself. Deliberately keyword/skill-matching-based rather than
pure semantic-embedding similarity: real-world ATS software (Workday, Taleo,
iCIMS, etc.) is overwhelmingly keyword-matching based, so this is a more
honest simulation of what actually screens a resume than an embedding score
would be. TF-IDF cosine similarity is layered on as a secondary signal to
catch overall topical relevance beyond exact keyword hits — and it runs
fully locally (scikit-learn), unlike sentence-transformers, which needs a
model download from a host this build environment can't reach.

Strengths/weak-areas/suggestions are rule-based templates, not LLM prose.
Documented as such — see README "Resume parser — known limitations", same
honesty standard applied here.
"""

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai.skills_taxonomy import SKILL_CATEGORIES
from app.services.ats.jd_requirements import extract_jd_skills

REQUIRED_WEIGHT = 0.8
PREFERRED_WEIGHT = 0.2
SKILL_MATCH_WEIGHT = 0.7
SIMILARITY_WEIGHT = 0.3


def _category_match(resume_skills: dict, jd_skills: dict) -> tuple[dict, dict, float]:
    matched, missing = {}, {}
    total_required, total_matched = 0, 0

    for category in SKILL_CATEGORIES:
        jd_set = set(jd_skills.get(category, []))
        resume_set = set(resume_skills.get(category, []))
        matched[category] = sorted(jd_set & resume_set)
        missing[category] = sorted(jd_set - resume_set)
        total_required += len(jd_set)
        total_matched += len(jd_set & resume_set)

    percent = (total_matched / total_required * 100) if total_required else 100.0
    return matched, missing, round(percent, 1)


def compute_semantic_similarity(resume_text: str, jd_text: str) -> float:
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    try:
        tfidf = vectorizer.fit_transform([resume_text, jd_text])
    except ValueError:
        return 0.0  # e.g. both texts are entirely stopwords — degenerate input
    return round(float(cosine_similarity(tfidf[0], tfidf[1])[0][0]) * 100, 1)


def _all_taxonomy_terms_lower() -> set[str]:
    terms = set()
    for skills in SKILL_CATEGORIES.values():
        for name, aliases in skills.items():
            terms.add(name.lower())
            terms.update(a.lower() for a in aliases)
    return terms


JD_BOILERPLATE_STOPWORDS = {
    "experience", "strong", "years", "year", "join", "team", "growing", "looking",
    "role", "responsibilities", "work", "working", "environment", "opportunity",
    "candidate", "candidates", "skills", "ability", "knowledge", "understanding",
    "familiarity", "including", "etc", "plus", "using", "use", "needed", "required",
    "requirements", "requirement", "preferred", "qualifications", "qualification",
}


def extract_missing_keywords(resume_text: str, jd_text: str, top_n: int = 15) -> list[str]:
    """The JD's highest-TF-IDF-weighted single words that don't appear in the
    resume at all — catches domain vocabulary the fixed skill taxonomy
    doesn't cover (a specific methodology, product name, industry term),
    rather than only ever comparing against the closed skills list.

    Unigrams only: bigrams looked appealing at first (e.g. "container
    orchestration") but mostly produced noise fragments like "aws docker" or
    "django experience" that slip past the exact-term taxonomy filter below
    even though "aws"/"docker"/"django" alone are already-matched skills.
    """
    if not jd_text.strip():
        return []
    taxonomy_terms = _all_taxonomy_terms_lower()
    stop_words = list(ENGLISH_STOP_WORDS | JD_BOILERPLATE_STOPWORDS)
    vectorizer = TfidfVectorizer(stop_words=stop_words, max_features=100, ngram_range=(1, 1))
    try:
        tfidf = vectorizer.fit_transform([jd_text])
    except ValueError:
        return []

    scores = tfidf.toarray()[0]
    terms_by_score = sorted(zip(vectorizer.get_feature_names_out(), scores), key=lambda t: -t[1])

    resume_lower = resume_text.lower()
    missing = []
    for term, score in terms_by_score:
        if score <= 0 or term in taxonomy_terms:
            continue
        if term not in resume_lower:
            missing.append(term)
        if len(missing) >= top_n:
            break
    return missing


def _generate_strengths(matched_required: dict, resume_analysis: dict) -> list[str]:
    strengths = []
    for category, skills in matched_required.items():
        if skills:
            label = category.replace("_", " ")
            strengths.append(f"Strong match on {label}: {', '.join(skills[:5])}")
    if resume_analysis.get("links", {}).get("github"):
        strengths.append("GitHub profile linked — recruiters can verify hands-on work")
    if resume_analysis.get("links", {}).get("linkedin"):
        strengths.append("LinkedIn profile linked")
    if len(resume_analysis.get("experience", [])) >= 2:
        strengths.append(f"{len(resume_analysis['experience'])} work experience entries detected")
    if any(cert for cert in resume_analysis.get("skills", {}).get("certifications", [])):
        strengths.append("Relevant certifications present")
    return strengths or ["No strong keyword matches found against this job description yet"]


def _generate_weak_areas(missing_required: dict) -> list[str]:
    weak = []
    for category, skills in missing_required.items():
        if skills:
            label = category.replace("_", " ")
            weak.append(f"Missing required {label}: {', '.join(skills[:5])}")
    return weak


def _generate_formatting_suggestions(resume_analysis: dict, raw_text: str) -> list[str]:
    suggestions = []
    if not any(char.isdigit() for entry in resume_analysis.get("experience", []) for char in (entry.get("description") or "")):
        suggestions.append("Add measurable achievements with numbers (e.g. \"reduced latency by 30%\") — quantified impact scores better with both ATS keyword scans and human reviewers")
    word_count = len(raw_text.split())
    if word_count < 150:
        suggestions.append("Resume looks short — ATS systems and recruiters both tend to penalize resumes that are too sparse to demonstrate depth")
    elif word_count > 1200:
        suggestions.append("Resume looks long — consider trimming to the most relevant experience for this specific role")
    if not resume_analysis.get("links", {}).get("github") and not resume_analysis.get("links", {}).get("portfolio"):
        suggestions.append("Consider adding a GitHub or portfolio link so reviewers can see real work, not just claims")
    return suggestions


def _generate_targeted_suggestions(missing_required: dict) -> dict[str, list[str]]:
    project_suggestions, cert_suggestions, experience_suggestions = [], [], []
    for category, skills in missing_required.items():
        for skill in skills[:3]:
            if category == "certifications":
                cert_suggestions.append(f"A {skill} certification would directly address a required qualification")
            elif category in ("programming_languages", "frameworks", "databases", "cloud"):
                project_suggestions.append(f"Add a project demonstrating {skill} — it's required by this JD but not evidenced in your resume")
            elif category == "soft_skills":
                experience_suggestions.append(f"Where you can, phrase a bullet point to explicitly demonstrate {skill}")
    return {
        "project_suggestions": project_suggestions,
        "certification_suggestions": cert_suggestions,
        "experience_suggestions": experience_suggestions,
    }


def score_resume_against_jd(resume_analysis: dict, resume_raw_text: str, jd_text: str) -> dict:
    jd_skills = extract_jd_skills(jd_text)
    resume_skills = resume_analysis.get("skills", {})

    matched_required, missing_required, required_match_pct = _category_match(resume_skills, jd_skills["required"])
    matched_preferred, missing_preferred, preferred_match_pct = (
        _category_match(resume_skills, jd_skills["preferred"]) if jd_skills["preferred"] else ({}, {}, 100.0)
    )

    skill_match_percent = round(REQUIRED_WEIGHT * required_match_pct + PREFERRED_WEIGHT * preferred_match_pct, 1)
    similarity_score = compute_semantic_similarity(resume_raw_text, jd_text)
    ats_score = round(SKILL_MATCH_WEIGHT * skill_match_percent + SIMILARITY_WEIGHT * similarity_score, 1)

    all_missing_skills = {
        cat: sorted(set(missing_required.get(cat, [])) | set(missing_preferred.get(cat, [])))
        for cat in SKILL_CATEGORIES
    }
    missing_keywords = extract_missing_keywords(resume_raw_text, jd_text)
    targeted = _generate_targeted_suggestions(missing_required)

    return {
        "ats_score": min(ats_score, 100.0),
        "skill_match_percent": skill_match_percent,
        "semantic_similarity_percent": similarity_score,
        "matched_skills": matched_required,
        "missing_skills": all_missing_skills,
        "missing_keywords": missing_keywords,
        "strengths": _generate_strengths(matched_required, resume_analysis),
        "weak_areas": _generate_weak_areas(missing_required),
        "formatting_suggestions": _generate_formatting_suggestions(resume_analysis, resume_raw_text),
        **targeted,
    }

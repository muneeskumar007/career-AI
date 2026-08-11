from app.services.report.resume_score import compute_resume_completeness_score


def test_full_resume_scores_highly():
    analysis = {
        "summary": "Experienced engineer.",
        "experience": [{"description": "Did things."}, {"description": "Did more things."}],
        "education": [{"degree": "B.S"}],
        "projects": [{"name": "Project"}],
        "skills": {
            "programming_languages": ["Python"], "frameworks": ["FastAPI"],
            "databases": ["PostgreSQL"], "certifications": ["AWS Certified Solutions Architect"],
        },
        "links": {"github": "https://github.com/x", "linkedin": None, "portfolio": None},
    }
    result = compute_resume_completeness_score(analysis)
    assert result["score"] == 100


def test_empty_resume_scores_zero():
    analysis = {"summary": None, "experience": [], "education": [], "projects": [], "skills": {}, "links": {}}
    result = compute_resume_completeness_score(analysis)
    assert result["score"] == 0
    assert all(not c["passed"] for c in result["checks"])


def test_partial_resume_scores_in_between():
    analysis = {
        "summary": "A summary.",
        "experience": [{"description": None}],  # has experience but no description — two different checks
        "education": [],
        "projects": [],
        "skills": {"programming_languages": ["Python"]},
        "links": {},
    }
    result = compute_resume_completeness_score(analysis)
    assert 0 < result["score"] < 100
    checks_by_label = {c["label"]: c["passed"] for c in result["checks"]}
    assert checks_by_label["Has a summary"] is True
    assert checks_by_label["Has work experience listed"] is True
    assert checks_by_label["Experience entries have descriptions"] is False
    assert checks_by_label["Has education listed"] is False

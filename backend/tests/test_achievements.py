from app.services.achievements import compute_achievements


def _empty_stats(**overrides):
    base = {
        "resume_count": 0, "completed_interview_count": 0, "ats_comparison_count": 0,
        "best_resume_score": None, "best_interview_score": None,
    }
    base.update(overrides)
    return base


def _by_id(achievements):
    return {a["id"]: a["unlocked"] for a in achievements}


def test_no_activity_unlocks_nothing():
    result = compute_achievements(_empty_stats())
    assert all(not unlocked for unlocked in _by_id(result).values())


def test_first_resume_unlocks_after_one_upload():
    result = _by_id(compute_achievements(_empty_stats(resume_count=1)))
    assert result["first_resume"] is True
    assert result["first_interview"] is False


def test_first_interview_requires_completed_not_just_started():
    result = _by_id(compute_achievements(_empty_stats(completed_interview_count=0)))
    assert result["first_interview"] is False

    result = _by_id(compute_achievements(_empty_stats(completed_interview_count=1)))
    assert result["first_interview"] is True


def test_five_interviews_requires_five_not_four():
    result = _by_id(compute_achievements(_empty_stats(completed_interview_count=4)))
    assert result["five_interviews"] is False

    result = _by_id(compute_achievements(_empty_stats(completed_interview_count=5)))
    assert result["five_interviews"] is True


def test_strong_resume_threshold():
    result = _by_id(compute_achievements(_empty_stats(best_resume_score=79)))
    assert result["strong_resume"] is False

    result = _by_id(compute_achievements(_empty_stats(best_resume_score=80)))
    assert result["strong_resume"] is True


def test_strong_interview_threshold():
    result = _by_id(compute_achievements(_empty_stats(best_interview_score=79.9)))
    assert result["strong_interview"] is False

    result = _by_id(compute_achievements(_empty_stats(best_interview_score=80.0)))
    assert result["strong_interview"] is True


def test_all_achievements_unlock_with_strong_full_activity():
    stats = _empty_stats(
        resume_count=3, completed_interview_count=5, ats_comparison_count=2,
        best_resume_score=95, best_interview_score=88,
    )
    result = _by_id(compute_achievements(stats))
    assert all(result.values())

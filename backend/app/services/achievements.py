"""
Achievement/badge computation — a pure function over aggregate stats, kept
separate from the DB-querying dashboard service so the unlock rules
themselves are trivially unit-testable without touching Mongo.
"""

ACHIEVEMENT_DEFINITIONS = [
    {"id": "first_resume", "label": "Getting Started", "description": "Upload your first resume", "check": lambda s: s["resume_count"] >= 1},
    {"id": "first_interview", "label": "Into the Arena", "description": "Complete your first mock interview", "check": lambda s: s["completed_interview_count"] >= 1},
    {"id": "five_interviews", "label": "Building the Habit", "description": "Complete 5 mock interviews", "check": lambda s: s["completed_interview_count"] >= 5},
    {"id": "first_ats_comparison", "label": "Know Your Odds", "description": "Run your first ATS comparison", "check": lambda s: s["ats_comparison_count"] >= 1},
    {"id": "strong_resume", "label": "Resume Ready", "description": "Reach a resume completeness score of 80+", "check": lambda s: (s.get("best_resume_score") or 0) >= 80},
    {"id": "strong_interview", "label": "Interview Sharp", "description": "Score 80+ overall in a completed interview", "check": lambda s: (s.get("best_interview_score") or 0) >= 80},
]


def compute_achievements(stats: dict) -> list[dict]:
    return [
        {"id": a["id"], "label": a["label"], "description": a["description"], "unlocked": bool(a["check"](stats))}
        for a in ACHIEVEMENT_DEFINITIONS
    ]

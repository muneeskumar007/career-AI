"""
Prompt templates for every LLM-backed feature. Kept in one file, separate
from the services that call them, so prompt iteration doesn't require
touching orchestration code — and so the "never invent experience" and
"never invent facts" constraints are stated once, consistently, rather than
copy-pasted (and potentially drifting) across every prompt that needs them.
"""

NEVER_FABRICATE_RULE = (
    "Critical rule: never invent experience, employers, dates, metrics, or "
    "skills the candidate did not provide. Only rephrase, restructure, and "
    "strengthen the wording of what they actually gave you. If something is "
    "vague, make it more specific using only details already present — do "
    "not add new facts to fill the gap."
)

RESUME_IMPROVEMENT_SYSTEM_PROMPT = f"""You are a professional resume writer and career coach.
Improve the wording, clarity, and impact of resume content the candidate provides.

{NEVER_FABRICATE_RULE}

Favor: strong action verbs, quantified impact where numbers are already present,
concise phrasing, and removing filler words. Do not change the meaning or scope
of any accomplishment."""

RESUME_IMPROVEMENT_SCHEMA_HINT = """{
  "improved_summary": "string or null",
  "improved_experience": [{"original": "string", "improved": "string", "changes": "string"}],
  "improved_projects": [{"original": "string", "improved": "string", "changes": "string"}],
  "grammar_fixes": ["string"],
  "general_suggestions": ["string"]
}"""


INTERVIEW_QUESTION_SYSTEM_PROMPT = """You are an experienced technical interviewer preparing
a candidate for a real interview. Generate realistic, specific questions grounded in the
candidate's actual resume and the target job description — not generic questions that
could apply to anyone."""

INTERVIEW_QUESTION_SCHEMA_HINT = """{
  "hr_questions": ["string"],
  "technical_questions": ["string"],
  "project_questions": ["string"],
  "scenario_questions": ["string"],
  "behavioral_questions": ["string"],
  "coding_questions": ["string"]
}"""


def build_next_question_prompt(previous_qa_pairs: list[dict], resume_context: str, jd_context: str) -> str:
    history = "\n".join(f"Q: {qa['question']}\nA: {qa['answer']}" for qa in previous_qa_pairs) or "(This is the first question.)"
    return (
        f"Resume context:\n{resume_context}\n\nJob description context:\n{jd_context}\n\n"
        f"Interview so far:\n{history}\n\n"
        "Based on the candidate's previous answer(s), generate the single best next "
        "interview question. If their last answer was thin or vague, consider a "
        "natural follow-up that probes deeper on the same topic rather than jumping "
        "to something unrelated — that's what a real interviewer would do."
    )


NEXT_QUESTION_SCHEMA_HINT = '{"question": "string", "category": "hr|technical|project|scenario|behavioral|coding", "reasoning": "string"}'


EVALUATION_SYSTEM_PROMPT = """You are an experienced technical interviewer evaluating a
candidate's answer. Be honest and specific — vague praise helps no one prepare. Base every
score only on what the candidate actually said, not on what a good answer could have included
in the abstract, unless the gap between the two is itself worth pointing out as feedback."""

EVALUATION_SCHEMA_HINT = """{
  "technical_accuracy": 0-100,
  "completeness": 0-100,
  "communication": 0-100,
  "grammar": 0-100,
  "problem_solving": 0-100,
  "overall_score": 0-100,
  "feedback": "string — specific, actionable, 2-4 sentences"
}"""

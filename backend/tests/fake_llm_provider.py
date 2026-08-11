"""
A test double for LLMProvider. Every AI-backed service (resume improvement,
question generation, interview flow, evaluation) accepts an injected
provider — this fake lets tests verify the full orchestration (prompt
building -> provider call -> schema validation -> persistence -> error
handling) without a real Gemini/Ollama API key.

What this fake does NOT prove: that a real LLM's output would actually be
good, well-formed, or match the schema on the first try. That's a live-model
concern, documented as untested in the README rather than glossed over here.
"""

from app.ai.providers.base import LLMProvider, LLMProviderError


class FakeLLMProvider(LLMProvider):
    def __init__(self, json_responses=None, text_response="Improved text.", raise_error=False, response_map=None):
        """json_responses: a single dict (returned every call) or a list of
        dicts (returned in order, one per call).

        response_map: dict[str, dict] keyed by a substring to look for in
        schema_hint — lets ONE fake instance correctly serve services that
        expect different response shapes (e.g. the interview flow, where
        AdaptiveQuestionService and AnswerEvaluatorService share one injected
        provider and their calls interleave, so a simple ordered list can't
        tell which shape is expected next). Checked before json_responses.
        """
        self.json_responses = json_responses
        self.response_map = response_map or {}
        self.text_response = text_response
        self.raise_error = raise_error
        self.call_count = 0
        self.last_system_prompt = None
        self.last_user_prompt = None
        self.last_schema_hint = None

    async def generate_json(self, system_prompt: str, user_prompt: str, schema_hint: str) -> dict:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        self.last_schema_hint = schema_hint
        if self.raise_error:
            raise LLMProviderError("Simulated provider failure")

        self.call_count += 1
        for marker, response in self.response_map.items():
            if marker in schema_hint:
                return response

        if isinstance(self.json_responses, list):
            return self.json_responses[min(self.call_count - 1, len(self.json_responses) - 1)]
        return self.json_responses

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if self.raise_error:
            raise LLMProviderError("Simulated provider failure")
        self.call_count += 1
        return self.text_response


FAKE_RESUME_IMPROVEMENT_RESPONSE = {
    "improved_summary": "Results-driven backend engineer with 5 years building scalable APIs.",
    "improved_experience": [
        {
            "original": "Led migration of monolith to microservices using Python and Docker.",
            "improved": "Led the migration of a monolithic system to microservices architecture using Python and Docker, improving deployment velocity.",
            "changes": "Strengthened the verb and added a concrete outcome phrase.",
        }
    ],
    "improved_projects": [
        {
            "original": "React and FastAPI app with PostgreSQL backend.",
            "improved": "Built a full-stack personal finance tracker using React, FastAPI, and PostgreSQL, deployed with Docker and Kubernetes on AWS.",
            "changes": "Made the tech stack and deployment details more prominent.",
        }
    ],
    "grammar_fixes": ["No major grammar issues found."],
    "general_suggestions": ["Consider adding quantified metrics to the Globex Inc role."],
}

FAKE_QUESTION_SET_RESPONSE = {
    "hr_questions": ["Why are you interested in this role?", "Where do you see yourself in 5 years?"],
    "technical_questions": ["Walk me through how you'd design a rate limiter.", "Explain the tradeoffs between SQL and NoSQL."],
    "project_questions": ["Tell me about the Personal Finance Tracker project.", "What was the hardest bug you fixed in that project?"],
    "scenario_questions": ["A production service is down — walk me through your response.", "How would you handle a disagreement with a teammate on architecture?"],
    "behavioral_questions": ["Tell me about a time you mentored someone.", "Describe a project that didn't go as planned."],
    "coding_questions": ["Reverse a linked list.", "Find the first non-repeating character in a string."],
}

FAKE_NEXT_QUESTION_RESPONSE = {
    "question": "Can you walk me through a technical decision you're proud of?",
    "category": "technical",
    "reasoning": "Opens broadly to see where the candidate's strengths are.",
}

FAKE_EVALUATION_RESPONSE = {
    "technical_accuracy": 78.0,
    "completeness": 70.0,
    "communication": 85.0,
    "grammar": 90.0,
    "problem_solving": 75.0,
    "overall_score": 79.6,
    "feedback": "Solid technical explanation with clear structure; could go deeper on tradeoffs.",
}

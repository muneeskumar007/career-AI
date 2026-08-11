"""
Curated difficulty/resource/time-estimate metadata for skills in the
taxonomy (app/ai/skills_taxonomy.py). Deliberately a hand-maintained table
rather than an LLM guess: for "how long does it take to learn Docker",
a small curated table a human can review and correct is more trustworthy
than a per-request model call that might invent a plausible-sounding but
wrong answer. Skills without an entry fall back to reasonable defaults
(see skill_gap_service.py) rather than raising an error — the taxonomy will
keep growing and every new skill added there shouldn't require an entry
here just to keep working.

difficulty: Beginner | Intermediate | Advanced
estimated_time: rough, for someone with adjacent-skill background — a
backend engineer learning a new backend framework is faster than someone
learning their first programming concept entirely.
"""

SKILL_METADATA = {
    # Programming languages
    "Python": {"difficulty": "Beginner", "resource": "https://docs.python.org/3/tutorial/", "estimated_time": "2-4 weeks"},
    "JavaScript": {"difficulty": "Beginner", "resource": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "estimated_time": "3-5 weeks"},
    "TypeScript": {"difficulty": "Intermediate", "resource": "https://www.typescriptlang.org/docs/", "estimated_time": "2-3 weeks"},
    "Java": {"difficulty": "Intermediate", "resource": "https://docs.oracle.com/javase/tutorial/", "estimated_time": "4-6 weeks"},
    "C++": {"difficulty": "Advanced", "resource": "https://en.cppreference.com/w/", "estimated_time": "8-12 weeks"},
    "Go": {"difficulty": "Intermediate", "resource": "https://go.dev/tour/", "estimated_time": "2-4 weeks"},
    "Rust": {"difficulty": "Advanced", "resource": "https://doc.rust-lang.org/book/", "estimated_time": "6-10 weeks"},
    "SQL": {"difficulty": "Beginner", "resource": "https://mode.com/sql-tutorial/", "estimated_time": "2-3 weeks"},
    # Frameworks
    "React": {"difficulty": "Intermediate", "resource": "https://react.dev/learn", "estimated_time": "3-5 weeks"},
    "Django": {"difficulty": "Intermediate", "resource": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "estimated_time": "3-4 weeks"},
    "FastAPI": {"difficulty": "Beginner", "resource": "https://fastapi.tiangolo.com/tutorial/", "estimated_time": "1-2 weeks"},
    "Flask": {"difficulty": "Beginner", "resource": "https://flask.palletsprojects.com/en/latest/quickstart/", "estimated_time": "1-2 weeks"},
    "Next.js": {"difficulty": "Intermediate", "resource": "https://nextjs.org/learn", "estimated_time": "2-4 weeks"},
    "Node.js": {"difficulty": "Beginner", "resource": "https://nodejs.org/en/learn", "estimated_time": "2-4 weeks"},
    "Spring": {"difficulty": "Advanced", "resource": "https://spring.io/guides", "estimated_time": "6-8 weeks"},
    "TensorFlow": {"difficulty": "Advanced", "resource": "https://www.tensorflow.org/tutorials", "estimated_time": "6-10 weeks"},
    "PyTorch": {"difficulty": "Advanced", "resource": "https://pytorch.org/tutorials/", "estimated_time": "6-10 weeks"},
    # Databases
    "PostgreSQL": {"difficulty": "Intermediate", "resource": "https://www.postgresql.org/docs/current/tutorial.html", "estimated_time": "2-3 weeks"},
    "MongoDB": {"difficulty": "Beginner", "resource": "https://www.mongodb.com/docs/manual/tutorial/", "estimated_time": "1-2 weeks"},
    "MySQL": {"difficulty": "Beginner", "resource": "https://dev.mysql.com/doc/mysql-tutorial-excerpt/en/", "estimated_time": "1-2 weeks"},
    "Redis": {"difficulty": "Beginner", "resource": "https://redis.io/docs/latest/develop/get-started/", "estimated_time": "1 week"},
    "Elasticsearch": {"difficulty": "Advanced", "resource": "https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html", "estimated_time": "4-6 weeks"},
    # Cloud/DevOps
    "AWS": {"difficulty": "Intermediate", "resource": "https://aws.amazon.com/getting-started/", "estimated_time": "4-8 weeks"},
    "Azure": {"difficulty": "Intermediate", "resource": "https://learn.microsoft.com/en-us/training/azure/", "estimated_time": "4-8 weeks"},
    "GCP": {"difficulty": "Intermediate", "resource": "https://cloud.google.com/docs/get-started", "estimated_time": "4-8 weeks"},
    "Docker": {"difficulty": "Beginner", "resource": "https://docs.docker.com/get-started/", "estimated_time": "1-2 weeks"},
    "Kubernetes": {"difficulty": "Advanced", "resource": "https://kubernetes.io/docs/tutorials/", "estimated_time": "6-10 weeks"},
    "Terraform": {"difficulty": "Intermediate", "resource": "https://developer.hashicorp.com/terraform/tutorials", "estimated_time": "3-5 weeks"},
    "CI/CD": {"difficulty": "Intermediate", "resource": "https://docs.github.com/en/actions/get-started", "estimated_time": "2-3 weeks"},
    "Git": {"difficulty": "Beginner", "resource": "https://git-scm.com/book/en/v2", "estimated_time": "1 week"},
    # Soft skills
    "Leadership": {"difficulty": "Advanced", "resource": None, "estimated_time": "Ongoing — best built through real project ownership, not a course"},
    "Communication": {"difficulty": "Intermediate", "resource": None, "estimated_time": "Ongoing — practice-driven"},
    "Project Management": {"difficulty": "Intermediate", "resource": "https://www.pmi.org/learning", "estimated_time": "4-6 weeks for fundamentals"},
    # Certifications
    "AWS Certified Solutions Architect": {"difficulty": "Advanced", "resource": "https://aws.amazon.com/certification/certified-solutions-architect-associate/", "estimated_time": "6-10 weeks of study"},
    "PMP": {"difficulty": "Advanced", "resource": "https://www.pmi.org/certifications/project-management-pmp", "estimated_time": "3-6 months of study"},
    "Certified Scrum Master": {"difficulty": "Beginner", "resource": "https://www.scrumalliance.org/get-certified/scrum-master-track/certified-scrummaster", "estimated_time": "1-2 weeks"},
}

DEFAULT_METADATA = {"difficulty": "Intermediate", "resource": None, "estimated_time": "4-6 weeks"}


def get_skill_metadata(skill_name: str) -> dict:
    return SKILL_METADATA.get(skill_name, DEFAULT_METADATA)

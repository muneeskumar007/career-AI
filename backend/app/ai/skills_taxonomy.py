"""
Keyword taxonomy for skill matching. Deliberately not ML-based: for a closed
vocabulary like "known programming languages," exact/alias matching against a
maintained list is more precise and far more debuggable than asking a model
to free-associate skills, and it's what actually runs in resume_parser.py.
The LLM-enhanced path (Module 3's ai/ hook, once a provider key is available)
is for open-ended judgment calls like project descriptions — not for this.

Extend by adding entries; each skill can have "aliases" for common variant
spellings so "Node.js" and "NodeJS" both match "Node.js" in the resume.
"""

PROGRAMMING_LANGUAGES = {
    "Python": [], "JavaScript": ["JS"], "TypeScript": ["TS"], "Java": [],
    "C++": ["Cpp"], "C#": ["CSharp", "C Sharp"], "C": [], "Go": ["Golang"],
    "Rust": [], "Ruby": [], "PHP": [], "Swift": [], "Kotlin": [], "Scala": [],
    "R": [], "MATLAB": [], "SQL": [], "Perl": [], "Dart": [], "Objective-C": [],
    "Shell": ["Bash", "Shell Scripting"], "PowerShell": [], "Haskell": [], "Lua": [],
}

FRAMEWORKS = {
    "React": ["React.js", "ReactJS"], "Angular": [], "Vue": ["Vue.js", "VueJS"],
    "Next.js": ["NextJS"], "Django": [], "Flask": [], "FastAPI": [],
    "Spring": ["Spring Boot"], "Express": ["Express.js"], ".NET": ["ASP.NET", "DotNet"],
    "Ruby on Rails": ["Rails"], "Laravel": [], "Node.js": ["NodeJS", "Node"],
    "jQuery": [], "Svelte": [], "Redux": [], "GraphQL": [], "TensorFlow": [],
    "PyTorch": [], "Scikit-learn": ["sklearn"], "Pandas": [], "NumPy": [],
    "Tailwind CSS": ["TailwindCSS", "Tailwind"], "Bootstrap": [],
}

DATABASES = {
    "MySQL": [], "PostgreSQL": ["Postgres"], "MongoDB": [], "Redis": [],
    "SQLite": [], "Oracle": ["Oracle DB"], "SQL Server": ["MSSQL"],
    "Cassandra": [], "DynamoDB": [], "Elasticsearch": [], "Firebase": [],
    "MariaDB": [], "Neo4j": [], "CouchDB": [],
}

CLOUD_DEVOPS = {
    "AWS": ["Amazon Web Services"], "Azure": ["Microsoft Azure"],
    "GCP": ["Google Cloud", "Google Cloud Platform"], "Docker": [],
    "Kubernetes": ["K8s"], "Terraform": [], "Jenkins": [], "CI/CD": ["CICD"],
    "GitHub Actions": [], "GitLab CI": [], "Ansible": [], "Nginx": [],
    "Linux": [], "Git": [],
}

SOFT_SKILLS = {
    "Leadership": [], "Communication": [], "Teamwork": ["Team Player"],
    "Problem Solving": [], "Time Management": [], "Adaptability": [],
    "Critical Thinking": [], "Collaboration": [], "Attention to Detail": [],
    "Creativity": [], "Conflict Resolution": [], "Mentoring": [],
    "Public Speaking": [], "Project Management": [], "Agile": ["Scrum"],
    "Stakeholder Management": [],
}

CERTIFICATIONS = {
    # Certification matching is strict by design (exact name or a registered
    # alias, same as every other category) — but real JDs very often phrase
    # this loosely ("AWS certification preferred" rather than the full
    # official title), which this taxonomy will legitimately miss. Add
    # common loose phrasings as aliases here as you encounter them; there's
    # no way to anticipate all of them upfront.
    "AWS Certified Solutions Architect": ["AWS Solutions Architect"],
    "AWS Certified Developer": [], "PMP": ["Project Management Professional"],
    "Certified Scrum Master": ["CSM"], "CISSP": [],
    "Google Cloud Professional": ["GCP Certified"],
    "Microsoft Certified": ["MCSA", "MCSE"], "CompTIA A+": [],
    "CKA": ["Certified Kubernetes Administrator"], "Six Sigma": [],
}

SKILL_CATEGORIES = {
    "programming_languages": PROGRAMMING_LANGUAGES,
    "frameworks": FRAMEWORKS,
    "databases": DATABASES,
    "cloud": CLOUD_DEVOPS,
    "soft_skills": SOFT_SKILLS,
    "certifications": CERTIFICATIONS,
}

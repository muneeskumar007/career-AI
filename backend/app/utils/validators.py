import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
PASSWORD_REQUIREMENTS_MESSAGE = (
    "Password must be at least 8 characters and include an uppercase letter, "
    "a lowercase letter, a number, and a special character"
)


def validate_password_strength(value: str) -> str:
    """Shared by every schema that accepts a new password, so the rule lives once."""
    if not PASSWORD_REGEX.match(value):
        raise ValueError(PASSWORD_REQUIREMENTS_MESSAGE)
    return value

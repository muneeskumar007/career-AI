import hashlib

import bcrypt


def _prehash(password: str) -> bytes:
    # bcrypt silently truncates inputs over 72 bytes. SHA-256 the password
    # first so arbitrarily long passwords are hashed safely and predictably,
    # then bcrypt the fixed-size digest for its slow, salted hashing.
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.config.settings import settings
from app.utils.exceptions import InvalidTokenException, TokenExpiredException

TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: TokenType,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_hex(8),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: str, token_version: int) -> str:
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
        extra_claims={"tv": token_version},
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        # Algorithm is pinned explicitly (never trust the token's own header)
        # to block "alg confusion" attacks.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidTokenException()

    if payload.get("type") != expected_type:
        raise InvalidTokenException()
    return payload

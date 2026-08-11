import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.settings import settings
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.email_service import EmailService
from app.utils.exceptions import (
    ForbiddenException,
    InvalidCredentialsException,
    InvalidResetTokenException,
    InvalidTokenException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.utils.security import hash_password, verify_password


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise InvalidTokenException()


def _serialize_user(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    return doc


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.email_service = EmailService()

    # --- Registration & login -------------------------------------------------

    async def register(self, payload: RegisterRequest) -> dict:
        existing = await self.users.find_one({"email": payload.email.lower()})
        if existing:
            raise UserAlreadyExistsException()

        now = datetime.now(timezone.utc)
        user_doc = {
            "name": payload.name,
            "email": payload.email.lower(),
            "password_hash": hash_password(payload.password),
            # role is never taken from client input — always starts as candidate;
            # promotion to recruiter/admin only happens via the admin-only endpoint.
            "role": UserRole.CANDIDATE.value,
            "is_active": True,
            "is_verified": False,
            "phone": None,
            "avatar_url": None,
            "reset_password_token_hash": None,
            "reset_password_expires_at": None,
            "refresh_token_version": 0,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
        }
        result = await self.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return _serialize_user(user_doc)

    async def authenticate(self, payload: LoginRequest) -> dict:
        user = await self.users.find_one({"email": payload.email.lower()})
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise InvalidCredentialsException()
        if not user.get("is_active", True):
            raise ForbiddenException("This account has been deactivated")

        await self.users.update_one(
            {"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(timezone.utc)}}
        )
        return _serialize_user(user)

    # --- Tokens -----------------------------------------------------------

    def issue_tokens(self, user: dict) -> tuple[str, str]:
        access_token = create_access_token(user_id=user["id"], role=user["role"])
        refresh_token = create_refresh_token(
            user_id=user["id"], token_version=user.get("refresh_token_version", 0)
        )
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token, expected_type="refresh")
        user = await self.users.find_one({"_id": _to_object_id(payload["sub"])})
        if not user:
            raise UserNotFoundException()
        # Token-version check lets logout / password-change invalidate every
        # outstanding refresh token at once without a server-side session store.
        if payload.get("tv") != user.get("refresh_token_version", 0):
            raise InvalidCredentialsException("Session has expired, please log in again")

        return self.issue_tokens(_serialize_user(user))

    async def invalidate_refresh_tokens(self, user_id: str) -> None:
        await self.users.update_one(
            {"_id": _to_object_id(user_id)}, {"$inc": {"refresh_token_version": 1}}
        )

    # --- Password reset -----------------------------------------------------

    async def request_password_reset(self, email: str) -> None:
        user = await self.users.find_one({"email": email.lower()})
        if not user:
            return  # never reveal whether an account exists

        raw_token = secrets.token_urlsafe(32)
        await self.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_password_token_hash": _hash_token(raw_token),
                    "reset_password_expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
                }
            },
        )
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        await self.email_service.send_password_reset_email(user["email"], reset_link)

    async def reset_password(self, token: str, new_password: str) -> None:
        user = await self.users.find_one({"reset_password_token_hash": _hash_token(token)})
        if not user or not user.get("reset_password_expires_at"):
            raise InvalidResetTokenException()

        expires_at = user["reset_password_expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise InvalidResetTokenException()

        await self.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "reset_password_token_hash": None,
                    "reset_password_expires_at": None,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {"refresh_token_version": 1},  # log out every existing session
            },
        )

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = await self.users.find_one({"_id": _to_object_id(user_id)})
        if not user:
            raise UserNotFoundException()
        if not verify_password(current_password, user["password_hash"]):
            raise InvalidCredentialsException("Current password is incorrect")

        await self.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password_hash": hash_password(new_password), "updated_at": datetime.now(timezone.utc)},
                "$inc": {"refresh_token_version": 1},
            },
        )

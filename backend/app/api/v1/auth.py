from fastapi import APIRouter, Cookie, Depends, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.config.settings import settings
from app.middleware.rate_limiter import limiter
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.exceptions import InvalidTokenException

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "careerai_refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


@router.post("/register", response_model=SuccessResponse[UserResponse], status_code=201)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(request: Request, payload: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(payload)
    return SuccessResponse(message="Account created successfully", data=UserResponse(**user))


@router.post("/login", response_model=SuccessResponse[TokenResponse])
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = AuthService(db)
    user = await service.authenticate(payload)
    access_token, refresh_token = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh_token)
    return SuccessResponse(
        message="Login successful",
        data=TokenResponse(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
    careerai_refresh_token: str | None = Cookie(default=None),
):
    if not careerai_refresh_token:
        raise InvalidTokenException("No refresh token provided")
    service = AuthService(db)
    access_token, new_refresh_token = await service.refresh_access_token(careerai_refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return SuccessResponse(
        message="Token refreshed",
        data=TokenResponse(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )


@router.post("/logout", response_model=SuccessResponse[None])
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    service = AuthService(db)
    await service.invalidate_refresh_tokens(current_user.id)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
    return SuccessResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=SuccessResponse[None])
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def forgot_password(
    request: Request, payload: ForgotPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = AuthService(db)
    await service.request_password_reset(payload.email)
    return SuccessResponse(message="If an account exists with this email, a reset link has been sent")


@router.post("/reset-password", response_model=SuccessResponse[None])
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def reset_password(request: Request, payload: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    service = AuthService(db)
    await service.reset_password(payload.token, payload.new_password)
    return SuccessResponse(message="Password reset successfully")

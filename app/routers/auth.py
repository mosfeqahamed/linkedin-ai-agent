"""Auth endpoints.

Flows:

  1. Email + password registration with OTP email verification:
     /auth/register -> /auth/verify-email -> session JWT.
     /auth/login for returning users; /auth/resend-otp to re-send a code.

  2. /auth/linkedin/login -> /auth/linkedin/callback — connects a LinkedIn
     account (for posting) to an already-authenticated user.
"""

import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.deps import get_current_user
from app.models.email_verification import OtpPurpose
from app.models.oauth_state import OAuthState
from app.models.user import User, UserRole
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.security import create_session_token, encrypt_token, hash_secret, verify_secret
from app.services import linkedin
from app.services.email import send_otp_email
from app.services.otp import OtpCooldownError, OtpError, issue_otp, verify_otp

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_and_send_otp(
    email: str, purpose: OtpPurpose, *, suppress_errors: bool = False
) -> None:
    """Generate an OTP and email it.

    Translates service errors to HTTP errors. When `suppress_errors` is set,
    cooldown and send failures are logged and swallowed instead — used by
    endpoints that must not reveal whether an account exists.
    """
    try:
        otp = await issue_otp(email, purpose)
    except OtpCooldownError as e:
        if suppress_errors:
            return
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            str(e),
            headers={"Retry-After": str(e.retry_after_seconds)},
        ) from e
    try:
        await send_otp_email(email, otp, purpose)
    except Exception as e:
        log.exception("Failed to send OTP email to %s", email)
        if suppress_errors:
            return
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Could not send the verification email. Please try again shortly.",
        ) from e


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    settings = get_settings()
    existing = await User.find_one(User.email == req.email)

    if existing is not None and existing.is_verified:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists."
        )

    role = UserRole.ADMIN if settings.is_admin_email(req.email) else UserRole.USER

    if existing is None:
        user = User(
            email=req.email,
            name=req.name,
            password_hash=hash_secret(req.password),
            role=role,
        )
        await user.insert()
    else:
        # Unverified account re-registering — refresh its credentials.
        existing.name = req.name or existing.name
        existing.password_hash = hash_secret(req.password)
        existing.role = role
        existing.updated_at = datetime.now(UTC)
        await existing.save()

    await _issue_and_send_otp(req.email, OtpPurpose.SIGNUP)
    return MessageResponse(message="Verification code sent to your email.")


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(req: VerifyEmailRequest):
    user = await User.find_one(User.email == req.email)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account found for this email.")

    try:
        await verify_otp(req.email, OtpPurpose.SIGNUP, req.otp)
    except OtpError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    if not user.is_verified:
        user.is_verified = True
        user.updated_at = datetime.now(UTC)
        await user.save()

    return TokenResponse(access_token=create_session_token(str(user.id)))


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(req: ResendOtpRequest):
    user = await User.find_one(User.email == req.email)
    # Only act for accounts that genuinely need verification, but never reveal
    # whether the email exists.
    if user is not None and not user.is_verified:
        await _issue_and_send_otp(req.email, OtpPurpose.SIGNUP)
    return MessageResponse(
        message="If your account needs verification, a new code has been sent."
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await User.find_one(User.email == req.email)
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")

    if user is None or user.password_hash is None:
        raise invalid
    if not verify_secret(req.password, user.password_hash):
        raise invalid
    if not user.is_verified:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Please verify your email before logging in."
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been disabled.")

    return TokenResponse(access_token=create_session_token(str(user.id)))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(req: ForgotPasswordRequest):
    user = await User.find_one(User.email == req.email)
    # Only send to established (verified, password-based) accounts, but never
    # reveal whether the email is registered — always return the same message.
    if user is not None and user.is_verified and user.password_hash is not None:
        await _issue_and_send_otp(req.email, OtpPurpose.PASSWORD_RESET, suppress_errors=True)
    return MessageResponse(
        message="If that email is registered, a password reset code has been sent."
    )


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(req: ResetPasswordRequest):
    user = await User.find_one(User.email == req.email)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email or code.")

    try:
        await verify_otp(req.email, OtpPurpose.PASSWORD_RESET, req.otp)
    except OtpError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e

    user.password_hash = hash_secret(req.new_password)
    user.is_verified = True  # resetting via emailed code proves email ownership
    user.updated_at = datetime.now(UTC)
    await user.save()

    return TokenResponse(access_token=create_session_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        timezone=user.timezone,
        linkedin_connected=user.has_linkedin_connected,
    )


async def _new_oauth_state(user: User) -> str:
    state = secrets.token_urlsafe(32)
    await OAuthState(state=state, user_id=user.id).insert()
    return state


@router.get("/linkedin/login")
async def linkedin_login(user: User = Depends(get_current_user)):
    state = await _new_oauth_state(user)
    return RedirectResponse(linkedin.build_authorize_url(state))


@router.get("/linkedin/authorize-url")
async def linkedin_authorize_url(user: User = Depends(get_current_user)):
    """JSON variant of /linkedin/login — frontend gets the URL and navigates the browser."""
    state = await _new_oauth_state(user)
    return {"url": linkedin.build_authorize_url(state)}


@router.get("/linkedin/callback")
async def linkedin_callback(
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):
    settings = get_settings()

    # Always consume the state so it can't be reused, even on the error path.
    state_rec = await OAuthState.find_one(OAuthState.state == state)
    user_id = state_rec.user_id if state_rec else None
    if state_rec is not None:
        await state_rec.delete()

    if error:
        msg = error_description or error
        return RedirectResponse(
            f"{settings.primary_frontend_origin}/settings?linkedin_error={msg}"
        )

    if code is None:
        return RedirectResponse(
            f"{settings.primary_frontend_origin}/settings?linkedin_error=missing_code"
        )

    if user_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired OAuth state")

    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    token_resp = await linkedin.exchange_code_for_tokens(code)
    access_token = token_resp["access_token"]
    refresh_token = token_resp.get("refresh_token")
    expires_in = token_resp.get("expires_in", 0)

    info = await linkedin.fetch_userinfo(access_token)

    user.linkedin_user_id = info["sub"]
    user.linkedin_access_token_encrypted = encrypt_token(access_token)
    if refresh_token:
        user.linkedin_refresh_token_encrypted = encrypt_token(refresh_token)
    user.linkedin_token_expires_at = linkedin.expires_at_from(expires_in)
    if info.get("email") and not user.email:
        user.email = info["email"]
    if info.get("name") and not user.name:
        user.name = info["name"]
    user.updated_at = datetime.now(UTC)
    await user.save()

    return RedirectResponse(f"{settings.primary_frontend_origin}/settings?linkedin=connected")


@router.post("/linkedin/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def linkedin_disconnect(user: User = Depends(get_current_user)):
    user.linkedin_user_id = None
    user.linkedin_access_token_encrypted = None
    user.linkedin_refresh_token_encrypted = None
    user.linkedin_token_expires_at = None
    user.updated_at = datetime.now(UTC)
    await user.save()

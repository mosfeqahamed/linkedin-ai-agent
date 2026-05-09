"""Auth endpoints.

Two flows:

  1. /auth/dev-login (development only) — creates or fetches a User by email
     and returns a session JWT. Lets you test /generate and /posts before
     LinkedIn API approval comes through.

  2. /auth/linkedin/login -> /auth/linkedin/callback — production flow.
     Stores LinkedIn tokens (encrypted) on the User document.
"""

import secrets
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.deps import get_current_user
from app.models.user import User
from app.schemas import DevLoginRequest, TokenResponse, UserResponse
from app.security import create_session_token, encrypt_token
from app.services import linkedin


router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory OAuth state store. Fine for single-process dev.
# For prod with multiple workers, move this to Redis or a Mongo collection with TTL.
_oauth_states: dict[str, str] = {}


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(req: DevLoginRequest):
    settings = get_settings()
    if settings.environment != "development":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "dev-login is disabled outside development")

    user = await User.find_one(User.email == req.email)
    if user is None:
        user = User(email=req.email, name=req.name)
        await user.insert()
    elif req.name and not user.name:
        user.name = req.name
        await user.save()

    return TokenResponse(access_token=create_session_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        timezone=user.timezone,
        linkedin_connected=user.has_linkedin_connected,
    )


@router.get("/linkedin/login")
async def linkedin_login(user: User = Depends(get_current_user)):
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = str(user.id)
    return RedirectResponse(linkedin.build_authorize_url(state))


@router.get("/linkedin/authorize-url")
async def linkedin_authorize_url(user: User = Depends(get_current_user)):
    """JSON variant of /linkedin/login — frontend gets the URL and navigates the browser."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = str(user.id)
    return {"url": linkedin.build_authorize_url(state)}


@router.get("/linkedin/callback")
async def linkedin_callback(
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):
    settings = get_settings()

    # Always pop state so it can't be reused, even on the error path.
    user_id = _oauth_states.pop(state, None)

    if error:
        msg = error_description or error
        return RedirectResponse(
            f"{settings.frontend_origin}/settings?linkedin_error={msg}"
        )

    if code is None:
        return RedirectResponse(
            f"{settings.frontend_origin}/settings?linkedin_error=missing_code"
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

    return RedirectResponse(f"{settings.frontend_origin}/settings?linkedin=connected")


@router.post("/linkedin/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def linkedin_disconnect(user: User = Depends(get_current_user)):
    user.linkedin_user_id = None
    user.linkedin_access_token_encrypted = None
    user.linkedin_refresh_token_encrypted = None
    user.linkedin_token_expires_at = None
    user.updated_at = datetime.now(UTC)
    await user.save()

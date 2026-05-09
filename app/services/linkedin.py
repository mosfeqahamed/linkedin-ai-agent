"""LinkedIn OAuth 2.0 + UGC Post API.

Flow:
  1. Frontend hits /auth/linkedin/login → we redirect to LinkedIn authorize URL.
  2. LinkedIn redirects back to /auth/linkedin/callback with ?code=...
  3. We exchange the code for access_token + refresh_token.
  4. We fetch the user profile (sub, email, name) via /v2/userinfo (OpenID).
  5. Tokens are encrypted and stored on the User document.

Posting uses the UGC Posts endpoint with author = "urn:li:person:{sub}".
Requires the `w_member_social` scope, which needs LinkedIn app review.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import get_settings


LINKEDIN_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"

SCOPES = ["openid", "profile", "email", "w_member_social"]


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "state": state,
        "scope": " ".join(SCOPES),
    }
    return f"{LINKEDIN_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    settings = get_settings()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.linkedin_redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            LINKEDIN_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    settings = get_settings()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            LINKEDIN_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def publish_post(access_token: str, linkedin_user_id: str, text: str) -> str:
    """Publish a text post and return the LinkedIn post URN."""
    payload = {
        "author": f"urn:li:person:{linkedin_user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            LINKEDIN_UGC_POSTS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return resp.headers.get("x-restli-id") or resp.json().get("id", "")


def expires_at_from(expires_in_seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

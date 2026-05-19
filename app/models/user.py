from datetime import UTC, datetime
from enum import StrEnum

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(Document):
    email: Indexed(EmailStr, unique=True)
    name: str | None = None

    # Email + password auth
    password_hash: str | None = None
    is_verified: bool = False
    role: UserRole = UserRole.USER
    is_active: bool = True

    linkedin_user_id: str | None = None
    linkedin_access_token_encrypted: str | None = None
    linkedin_refresh_token_encrypted: str | None = None
    linkedin_token_expires_at: datetime | None = None

    timezone: str = "UTC"

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"

    @property
    def has_linkedin_connected(self) -> bool:
        return self.linkedin_access_token_encrypted is not None

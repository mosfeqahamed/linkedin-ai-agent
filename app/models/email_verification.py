from datetime import UTC, datetime
from enum import StrEnum

from beanie import Document
from pydantic import EmailStr, Field
from pymongo import IndexModel


class OtpPurpose(StrEnum):
    SIGNUP = "signup"
    PASSWORD_RESET = "password_reset"


class EmailVerification(Document):
    """A pending one-time-password challenge.

    One row per (email, purpose). Re-requesting an OTP replaces the row.
    Mongo's TTL index removes rows automatically once `expires_at` passes.
    """

    email: EmailStr
    purpose: OtpPurpose
    otp_hash: str
    expires_at: datetime
    attempts: int = 0
    last_sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "email_verifications"
        indexes = [
            IndexModel([("email", 1), ("purpose", 1)], unique=True),
            IndexModel("expires_at", expireAfterSeconds=0),
        ]

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= _aware(self.expires_at)


def _aware(dt: datetime) -> datetime:
    """Mongo round-trips datetimes as naive UTC; normalise for comparison."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

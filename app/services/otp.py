"""One-time-password issuing and verification.

Backed by the `email_verifications` collection. One pending OTP per
(email, purpose); re-requesting replaces it. OTPs are stored hashed.
"""

import secrets
from datetime import UTC, datetime, timedelta

from app.config import get_settings
from app.models.email_verification import EmailVerification, OtpPurpose
from app.security import hash_secret, verify_secret


class OtpError(Exception):
    """OTP verification failed (missing, expired, wrong, or exhausted)."""


class OtpCooldownError(Exception):
    """An OTP was requested again before the resend cooldown elapsed."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Please wait {retry_after_seconds}s before requesting another code.")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def generate_otp() -> str:
    n = get_settings().otp_length
    return "".join(secrets.choice("0123456789") for _ in range(n))


async def issue_otp(email: str, purpose: OtpPurpose) -> str:
    """Create or replace the pending OTP for (email, purpose).

    Returns the plain OTP (to be emailed). Raises OtpCooldownError if a code
    was sent within the configured resend cooldown.
    """
    settings = get_settings()
    now = datetime.now(UTC)

    existing = await EmailVerification.find_one(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
    )
    if existing is not None:
        elapsed = (now - _aware(existing.last_sent_at)).total_seconds()
        if elapsed < settings.otp_resend_cooldown_seconds:
            raise OtpCooldownError(int(settings.otp_resend_cooldown_seconds - elapsed) + 1)

    otp = generate_otp()
    expires_at = now + timedelta(minutes=settings.otp_expire_minutes)

    if existing is None:
        await EmailVerification(
            email=email,
            purpose=purpose,
            otp_hash=hash_secret(otp),
            expires_at=expires_at,
            last_sent_at=now,
        ).insert()
    else:
        existing.otp_hash = hash_secret(otp)
        existing.expires_at = expires_at
        existing.attempts = 0
        existing.last_sent_at = now
        await existing.save()

    return otp


async def verify_otp(email: str, purpose: OtpPurpose, otp: str) -> None:
    """Check a submitted OTP. Consumes the record on success.

    Raises OtpError on any failure.
    """
    settings = get_settings()
    rec = await EmailVerification.find_one(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
    )
    if rec is None:
        raise OtpError("No verification code found. Please request a new one.")

    if rec.is_expired:
        await rec.delete()
        raise OtpError("This code has expired. Please request a new one.")

    if rec.attempts >= settings.otp_max_attempts:
        await rec.delete()
        raise OtpError("Too many incorrect attempts. Please request a new code.")

    if not verify_secret(otp, rec.otp_hash):
        rec.attempts += 1
        await rec.save()
        remaining = settings.otp_max_attempts - rec.attempts
        raise OtpError(f"Incorrect code. {remaining} attempt(s) remaining.")

    await rec.delete()

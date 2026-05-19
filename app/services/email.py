"""Email delivery.

Two modes, selected by `EMAIL_MODE`:
  - console : OTP codes are printed to the server log (no setup, for testing).
  - smtp    : real emails via SMTP (e.g. Gmail with an App Password).
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings
from app.models.email_verification import OtpPurpose

log = logging.getLogger(__name__)


def _compose(otp: str, purpose: OtpPurpose, expire_minutes: int) -> tuple[str, str]:
    if purpose == OtpPurpose.SIGNUP:
        subject = "Verify your LinkedIn AI Agent account"
        intro = "Welcome to LinkedIn AI Agent! Use this code to verify your email:"
    else:
        subject = "Reset your LinkedIn AI Agent password"
        intro = "Use this code to reset your password:"

    body = (
        f"{intro}\n\n"
        f"    {otp}\n\n"
        f"This code expires in {expire_minutes} minutes.\n"
        f"If you didn't request this, you can safely ignore this email.\n"
    )
    return subject, body


def _send_smtp(to_email: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = settings.email_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_otp_email(to_email: str, otp: str, purpose: OtpPurpose) -> None:
    """Deliver an OTP. Raises on SMTP failure so the caller can report it."""
    settings = get_settings()
    subject, body = _compose(otp, purpose, settings.otp_expire_minutes)

    if settings.email_mode == "console":
        # print() (not logging) so the code is always visible regardless of
        # uvicorn's log configuration.
        print(
            "\n"
            "  +----------------------------------------------+\n"
            "  |  EMAIL (console mode) - not actually sent    |\n"
            f"  |  To:      {to_email:<35}|\n"
            f"  |  Purpose: {purpose.value:<35}|\n"
            f"  |  OTP:     {otp:<35}|\n"
            "  +----------------------------------------------+\n",
            flush=True,
        )
        return

    await asyncio.to_thread(_send_smtp, to_email, subject, body)
    log.info("Sent %s OTP email to %s", purpose.value, to_email)

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "linkedin-ai-agent"
    environment: str = "development"
    debug: bool = True

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "linkedin_agent"

    deepseek_api_key: str = Field(..., description="DeepSeek API key")
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/auth/linkedin/callback"

    # Optional — raises the GitHub API rate limit from 60 to 5000 req/hr.
    github_token: str = ""

    jwt_secret: str = Field(..., description="Secret for signing session JWTs")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    fernet_key: str = Field(..., description="Base64 Fernet key for encrypting OAuth tokens at rest")

    frontend_origin: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Email / OTP
    email_mode: str = "console"  # "console" | "smtp"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""

    otp_length: int = 6
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60

    # Admin bootstrap — emails listed here become admins on registration.
    admin_emails: Annotated[list[str], NoDecode] = []

    @field_validator("frontend_origin", "admin_emails", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def primary_frontend_origin(self) -> str:
        return self.frontend_origin[0]

    def is_admin_email(self, email: str) -> bool:
        return email.lower() in {e.lower() for e in self.admin_emails}


@lru_cache
def get_settings() -> Settings:
    return Settings()

from datetime import UTC, datetime, timedelta

import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import get_settings


def hash_secret(plaintext: str) -> str:
    """Hash a password or OTP with bcrypt. bcrypt caps input at 72 bytes."""
    return bcrypt.hashpw(plaintext.encode()[:72], bcrypt.gensalt()).decode()


def verify_secret(plaintext: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode()[:72], hashed.encode())
    except ValueError:
        return False


def _fernet() -> Fernet:
    return Fernet(get_settings().fernet_key.encode())


def encrypt_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


def create_session_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_session_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None

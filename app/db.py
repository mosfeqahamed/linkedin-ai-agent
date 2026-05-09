from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import get_settings
from app.models.post import ScheduledPost
from app.models.user import User


_client: AsyncMongoClient | None = None


async def init_db() -> AsyncMongoClient:
    global _client
    settings = get_settings()
    _client = AsyncMongoClient(settings.mongodb_uri)
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=[User, ScheduledPost],
    )
    return _client


async def close_db() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_client() -> AsyncMongoClient:
    if _client is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    return _client

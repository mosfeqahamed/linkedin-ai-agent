from datetime import UTC, datetime

from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class RepoCache(Document):
    """Cached LLM analysis of a GitHub repository.

    Keyed by `owner/repo@version` (version derived from the repo's last push),
    so a new push naturally produces a new key. The TTL index drops entries
    after 24h to bound staleness.
    """

    repo_key: Indexed(str, unique=True)
    summary: str
    tech_stack: list[str] = []
    key_features: list[str] = []
    learning_modules: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "repo_cache"
        indexes = [
            IndexModel("created_at", expireAfterSeconds=86400),
        ]

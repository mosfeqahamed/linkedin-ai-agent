from datetime import UTC, datetime
from enum import StrEnum

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class PostStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost(Document):
    user_id: Indexed(PydanticObjectId)

    topic: str
    description: str | None = None
    generated_text: str

    scheduled_at: Indexed(datetime)
    status: Indexed(str) = PostStatus.DRAFT

    linkedin_post_urn: str | None = None
    error_message: str | None = None
    publish_attempts: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None

    class Settings:
        name = "scheduled_posts"

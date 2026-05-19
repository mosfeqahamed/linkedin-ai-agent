from datetime import UTC, datetime

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel


class OAuthState(Document):
    """A pending LinkedIn OAuth `state` token, tying a callback back to a user.

    Stored in Mongo (rather than process memory) so it survives across
    multiple workers/restarts. The TTL index expires unused states after
    10 minutes.
    """

    state: Indexed(str, unique=True)
    user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "oauth_states"
        indexes = [
            IndexModel("created_at", expireAfterSeconds=600),
        ]

from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

from app.models.post import PostStatus


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)


class GenerateResponse(BaseModel):
    generated_text: str


class CreatePostRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    generated_text: str = Field(..., min_length=1, max_length=3000)
    scheduled_at: datetime


class UpdatePostRequest(BaseModel):
    generated_text: str | None = Field(None, min_length=1, max_length=3000)
    scheduled_at: datetime | None = None


class PostResponse(BaseModel):
    id: PydanticObjectId
    topic: str
    description: str | None
    generated_text: str
    scheduled_at: datetime
    status: PostStatus
    linkedin_post_urn: str | None
    error_message: str | None
    publish_attempts: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class DevLoginRequest(BaseModel):
    email: EmailStr
    name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    name: str | None
    timezone: str
    linkedin_connected: bool

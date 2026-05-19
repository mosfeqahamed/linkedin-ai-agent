from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.models.post import PostStatus
from app.models.user import UserRole


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    github_url: HttpUrl | None = None
    # Subset of learning modules to emphasise on regeneration; None = use all.
    learning_modules: list[str] | None = None


class GenerateResponse(BaseModel):
    generated_text: str
    repo_summary: str | None = None
    tech_stack: list[str] = []
    learning_modules: list[str] = []


class CreatePostRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    generated_text: str = Field(..., min_length=1, max_length=3000)
    scheduled_at: datetime
    repo_url: str | None = Field(None, max_length=300)
    repo_summary: str | None = Field(None, max_length=2000)
    learning_modules: list[str] = []


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
    repo_url: str | None
    repo_summary: str | None
    learning_modules: list[str]
    linkedin_post_urn: str | None
    error_message: str | None
    publish_attempts: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(None, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{4,12}$")


class ResendOtpRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{4,12}$")
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    name: str | None
    role: UserRole
    is_verified: bool
    timezone: str
    linkedin_connected: bool


# ----- Admin -----

class AdminUserResponse(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    name: str | None
    role: UserRole
    is_verified: bool
    is_active: bool
    linkedin_connected: bool
    created_at: datetime
    post_count: int | None = None


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int


class AdminUpdateUserRequest(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AdminPostResponse(BaseModel):
    id: PydanticObjectId
    user_id: PydanticObjectId
    user_email: EmailStr | None
    topic: str
    status: PostStatus
    scheduled_at: datetime
    created_at: datetime
    error_message: str | None


class AdminPostListResponse(BaseModel):
    posts: list[AdminPostResponse]
    total: int


class AdminStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    admins: int
    linkedin_connected: int
    total_posts: int
    posts_by_status: dict[str, int]

"""Admin endpoints — user and post management.

Every route requires an authenticated user whose `role` is admin
(see `require_admin`). Admins are bootstrapped via the `ADMIN_EMAILS` setting.
"""

import logging
import re
from datetime import UTC, datetime

from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import require_admin
from app.models.post import PostStatus, ScheduledPost
from app.models.user import User, UserRole
from app.schemas import (
    AdminPostListResponse,
    AdminPostResponse,
    AdminStatsResponse,
    AdminUpdateUserRequest,
    AdminUserListResponse,
    AdminUserResponse,
)
from app.services.scheduler import cancel_scheduled_publish

log = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _user_to_response(user: User, post_count: int | None = None) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        is_active=user.is_active,
        linkedin_connected=user.has_linkedin_connected,
        created_at=user.created_at,
        post_count=post_count,
    )


@router.get("/stats", response_model=AdminStatsResponse)
async def stats(_admin: User = Depends(require_admin)):
    total_users = await User.find({}).count()
    verified_users = await User.find(User.is_verified == True).count()  # noqa: E712
    admins = await User.find(User.role == UserRole.ADMIN).count()
    linkedin_connected = await User.find(
        User.linkedin_access_token_encrypted != None  # noqa: E711
    ).count()
    total_posts = await ScheduledPost.find({}).count()

    agg = await ScheduledPost.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ).to_list()
    posts_by_status = {row["_id"]: row["count"] for row in agg}

    return AdminStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        admins=admins,
        linkedin_connected=linkedin_connected,
        total_posts=total_posts,
        posts_by_status=posts_by_status,
    )


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    search: str | None = Query(None, description="Case-insensitive email substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _admin: User = Depends(require_admin),
):
    query: dict = {}
    if search:
        query = {"email": {"$regex": re.escape(search), "$options": "i"}}

    total = await User.find(query).count()
    users = (
        await User.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
    )
    return AdminUserListResponse(
        users=[_user_to_response(u) for u in users],
        total=total,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(user_id: PydanticObjectId, _admin: User = Depends(require_admin)):
    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    post_count = await ScheduledPost.find(ScheduledPost.user_id == user_id).count()
    return _user_to_response(user, post_count)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: PydanticObjectId,
    req: AdminUpdateUserRequest,
    admin: User = Depends(require_admin),
):
    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Guard rails: an admin must not lock themselves out.
    if user.id == admin.id:
        if req.role is not None and req.role != UserRole.ADMIN:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "You cannot remove your own admin role."
            )
        if req.is_active is False:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "You cannot disable your own account."
            )

    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    user.updated_at = datetime.now(UTC)
    await user.save()

    post_count = await ScheduledPost.find(ScheduledPost.user_id == user_id).count()
    return _user_to_response(user, post_count)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: PydanticObjectId, admin: User = Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You cannot delete your own account."
        )
    user = await User.get(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # Hard delete: cancel scheduled publish jobs, drop the posts, then the user.
    posts = await ScheduledPost.find(ScheduledPost.user_id == user_id).to_list()
    for p in posts:
        cancel_scheduled_publish(str(p.id))
    await ScheduledPost.find(ScheduledPost.user_id == user_id).delete()
    await user.delete()
    log.info(
        "Admin %s hard-deleted user %s and %d post(s)",
        admin.email,
        user.email,
        len(posts),
    )


@router.get("/posts", response_model=AdminPostListResponse)
async def list_all_posts(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _admin: User = Depends(require_admin),
):
    query: dict = {}
    if status_filter:
        query = {"status": status_filter}

    total = await ScheduledPost.find(query).count()
    posts = (
        await ScheduledPost.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    user_ids = list({p.user_id for p in posts})
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    email_by_id = {u.id: u.email for u in users}

    return AdminPostListResponse(
        posts=[
            AdminPostResponse(
                id=p.id,
                user_id=p.user_id,
                user_email=email_by_id.get(p.user_id),
                topic=p.topic,
                status=PostStatus(p.status),
                scheduled_at=p.scheduled_at,
                created_at=p.created_at,
                error_message=p.error_message,
            )
            for p in posts
        ],
        total=total,
    )

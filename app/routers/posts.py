from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.models.post import PostStatus, ScheduledPost
from app.models.user import User
from app.schemas import CreatePostRequest, PostResponse, UpdatePostRequest
from app.services.deepseek import generate_post
from app.services.scheduler import cancel_scheduled_publish, schedule_publish

router = APIRouter(prefix="/posts", tags=["posts"])


def _to_response(post: ScheduledPost) -> PostResponse:
    return PostResponse(
        id=post.id,
        topic=post.topic,
        description=post.description,
        generated_text=post.generated_text,
        scheduled_at=post.scheduled_at,
        status=PostStatus(post.status),
        repo_url=post.repo_url,
        repo_summary=post.repo_summary,
        learning_modules=post.learning_modules,
        linkedin_post_urn=post.linkedin_post_urn,
        error_message=post.error_message,
        publish_attempts=post.publish_attempts,
        created_at=post.created_at,
        updated_at=post.updated_at,
        published_at=post.published_at,
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(req: CreatePostRequest, user: User = Depends(get_current_user)):
    scheduled_at = req.scheduled_at
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=UTC)
    if scheduled_at <= datetime.now(UTC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "scheduled_at must be in the future")

    post = ScheduledPost(
        user_id=user.id,
        topic=req.topic,
        description=req.description,
        generated_text=req.generated_text,
        scheduled_at=scheduled_at,
        status=PostStatus.SCHEDULED,
        repo_url=req.repo_url,
        repo_summary=req.repo_summary,
        learning_modules=req.learning_modules,
    )
    await post.insert()
    schedule_publish(str(post.id), scheduled_at)
    return _to_response(post)


@router.get("", response_model=list[PostResponse])
async def list_posts(user: User = Depends(get_current_user)):
    posts = await ScheduledPost.find(ScheduledPost.user_id == user.id).sort(
        "-scheduled_at"
    ).to_list()
    return [_to_response(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: PydanticObjectId, user: User = Depends(get_current_user)):
    post = await ScheduledPost.get(post_id)
    if post is None or post.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return _to_response(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: PydanticObjectId,
    req: UpdatePostRequest,
    user: User = Depends(get_current_user),
):
    post = await ScheduledPost.get(post_id)
    if post is None or post.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot edit a post in status '{post.status}'",
        )

    if req.generated_text is not None:
        post.generated_text = req.generated_text

    if req.scheduled_at is not None:
        new_at = req.scheduled_at
        if new_at.tzinfo is None:
            new_at = new_at.replace(tzinfo=UTC)
        if new_at <= datetime.now(UTC):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "scheduled_at must be in the future")
        post.scheduled_at = new_at
        schedule_publish(str(post.id), new_at)

    post.updated_at = datetime.now(UTC)
    await post.save()
    return _to_response(post)


@router.post("/{post_id}/regenerate", response_model=PostResponse)
async def regenerate_post(post_id: PydanticObjectId, user: User = Depends(get_current_user)):
    """Re-run DeepSeek on the original topic + description to get a new draft."""
    post = await ScheduledPost.get(post_id)
    if post is None or post.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot regenerate a post in status '{post.status}'",
        )

    # Re-use the stored repo analysis (if any) so regeneration stays on-topic
    # without another GitHub fetch.
    repo_analysis = None
    if post.repo_url and post.repo_summary:
        repo_analysis = {
            "summary": post.repo_summary,
            "tech_stack": [],
            "key_features": [],
            "learning_modules": post.learning_modules,
        }

    try:
        new_text = await generate_post(post.topic, post.description, repo_analysis)
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Generation failed: {e}")

    post.generated_text = new_text
    post.updated_at = datetime.now(UTC)
    await post.save()
    return _to_response(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: PydanticObjectId, user: User = Depends(get_current_user)):
    post = await ScheduledPost.get(post_id)
    if post is None or post.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.status in (PostStatus.PUBLISHING, PostStatus.PUBLISHED):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Cannot delete a post that is publishing or already published",
        )

    cancel_scheduled_publish(str(post.id))
    post.status = PostStatus.CANCELLED
    post.updated_at = datetime.now(UTC)
    await post.save()

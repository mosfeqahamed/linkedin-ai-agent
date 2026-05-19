"""APScheduler with MongoDBJobStore — survives restarts."""

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from beanie import PydanticObjectId
from pymongo import MongoClient

from app.config import get_settings
from app.models.post import PostStatus, ScheduledPost
from app.models.user import User
from app.security import decrypt_token, encrypt_token
from app.services.linkedin import (
    expires_at_from,
    publish_post,
    refresh_access_token,
)


log = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def init_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    sync_client = MongoClient(settings.mongodb_uri)
    jobstore = MongoDBJobStore(
        database=settings.mongodb_db_name,
        collection="apscheduler_jobs",
        client=sync_client,
    )
    _scheduler = AsyncIOScheduler(jobstores={"default": jobstore}, timezone="UTC")
    _scheduler.start()

    # Daily LinkedIn token refresh sweep at 03:00 UTC.
    # Tokens that expire within 7 days get refreshed proactively.
    _scheduler.add_job(
        _refresh_linkedin_tokens_job,
        trigger="cron",
        hour=3,
        minute=0,
        id="refresh:linkedin_tokens",
        replace_existing=True,
    )

    # Hourly sweep: remove accounts that were never email-verified within 24h.
    _scheduler.add_job(
        _cleanup_unverified_users_job,
        trigger="cron",
        minute=30,
        id="cleanup:unverified_users",
        replace_existing=True,
    )

    log.info("APScheduler started with MongoDBJobStore")
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def get_scheduler() -> AsyncIOScheduler:
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized — call init_scheduler() first")
    return _scheduler


def schedule_publish(post_id: str, run_at: datetime) -> None:
    scheduler = get_scheduler()
    scheduler.add_job(
        _publish_job,
        trigger="date",
        run_date=run_at,
        args=[post_id],
        id=f"publish:{post_id}",
        replace_existing=True,
        misfire_grace_time=300,
    )
    log.info("Scheduled publish for post %s at %s", post_id, run_at.isoformat())


def cancel_scheduled_publish(post_id: str) -> None:
    scheduler = get_scheduler()
    job_id = f"publish:{post_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        log.info("Cancelled scheduled publish for post %s", post_id)


async def _publish_job(post_id: str) -> None:
    """Idempotent publish worker. Marks status transitions in Mongo."""
    post = await ScheduledPost.get(PydanticObjectId(post_id))
    if post is None:
        log.warning("Post %s not found at publish time", post_id)
        return

    if post.status not in (PostStatus.SCHEDULED, PostStatus.FAILED):
        log.info("Post %s in status %s — skipping", post_id, post.status)
        return

    post.status = PostStatus.PUBLISHING
    post.publish_attempts += 1
    post.updated_at = datetime.now(UTC)
    await post.save()

    try:
        user = await User.get(post.user_id)
        if user is None or not user.has_linkedin_connected:
            raise RuntimeError("User has no LinkedIn connection")

        access_token = decrypt_token(user.linkedin_access_token_encrypted)
        urn = await publish_post(access_token, user.linkedin_user_id, post.generated_text)

        post.status = PostStatus.PUBLISHED
        post.linkedin_post_urn = urn
        post.published_at = datetime.now(UTC)
        post.error_message = None
    except Exception as e:
        log.exception("Publish failed for post %s", post_id)
        post.status = PostStatus.FAILED
        post.error_message = str(e)[:500]
    finally:
        post.updated_at = datetime.now(UTC)
        await post.save()


async def _cleanup_unverified_users_job() -> None:
    """Delete accounts that were never email-verified within 24h of registration."""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    result = await User.find(
        User.is_verified == False,  # noqa: E712
        User.created_at < cutoff,
    ).delete()
    deleted = getattr(result, "deleted_count", 0)
    if deleted:
        log.info("Cleaned up %s unverified account(s)", deleted)


async def _refresh_linkedin_tokens_job() -> None:
    """Refresh LinkedIn access tokens that are within 7 days of expiry."""
    threshold = datetime.now(UTC) + timedelta(days=7)
    users = await User.find(
        User.linkedin_refresh_token_encrypted != None,  # noqa: E711
        User.linkedin_token_expires_at < threshold,
    ).to_list()

    for user in users:
        try:
            refresh_token = decrypt_token(user.linkedin_refresh_token_encrypted)
            resp = await refresh_access_token(refresh_token)
            user.linkedin_access_token_encrypted = encrypt_token(resp["access_token"])
            if resp.get("refresh_token"):
                user.linkedin_refresh_token_encrypted = encrypt_token(resp["refresh_token"])
            user.linkedin_token_expires_at = expires_at_from(resp.get("expires_in", 0))
            user.updated_at = datetime.now(UTC)
            await user.save()
            log.info("Refreshed LinkedIn token for user %s", user.id)
        except Exception:
            log.exception("Failed to refresh LinkedIn token for user %s", user.id)

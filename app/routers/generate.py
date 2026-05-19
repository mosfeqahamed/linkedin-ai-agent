import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.deps import get_current_user
from app.models.repo_cache import RepoCache
from app.models.user import User
from app.schemas import GenerateRequest, GenerateResponse
from app.services.deepseek import analyze_repo, generate_post
from app.services.github import GitHubError, RepoContext, fetch_repo_context

log = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


async def _get_repo_analysis(context: RepoContext) -> dict:
    """Return the repo analysis, using the 24h cache when available."""
    key = f"{context.owner}/{context.repo}@{context.version}"
    cached = await RepoCache.find_one(RepoCache.repo_key == key)
    if cached is not None:
        return {
            "summary": cached.summary,
            "tech_stack": cached.tech_stack,
            "key_features": cached.key_features,
            "learning_modules": cached.learning_modules,
        }

    analysis = await analyze_repo(context)
    try:
        await RepoCache(repo_key=key, **analysis).insert()
    except DuplicateKeyError:
        pass  # another request cached it first — harmless
    return analysis


@router.post("", response_model=GenerateResponse)
async def generate(req: GenerateRequest, _user: User = Depends(get_current_user)):
    analysis: dict | None = None

    if req.github_url:
        try:
            context = await fetch_repo_context(str(req.github_url))
        except GitHubError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e
        except Exception as e:
            log.exception("GitHub fetch failed")
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, f"Could not read the repository: {e}"
            ) from e
        analysis = await _get_repo_analysis(context)

    try:
        text = await generate_post(
            req.topic, req.description, analysis, req.learning_modules
        )
    except Exception as e:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Generation failed: {e}"
        ) from e

    return GenerateResponse(
        generated_text=text,
        repo_summary=analysis["summary"] if analysis else None,
        tech_stack=analysis["tech_stack"] if analysis else [],
        learning_modules=analysis["learning_modules"] if analysis else [],
    )

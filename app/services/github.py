"""GitHub repository fetching for the post-generation pipeline.

Uses plain HTTP — the public REST API plus the repo's metadata. No token is
required for public repositories; `GITHUB_TOKEN`, if set, only raises the
rate limit (60 -> 5000 requests/hour).
"""

import base64
import logging
import re
from dataclasses import dataclass

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 12_000


class GitHubError(Exception):
    """A repository could not be read (bad URL, private/missing, or rate-limited)."""


@dataclass
class RepoContext:
    owner: str
    repo: str
    version: str  # cache-busting token derived from the repo's last push
    description: str | None
    topics: list[str]
    languages: list[str]
    file_list: list[str]
    readme: str
    stars: int

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL."""
    m = re.search(r"github\.com[/:]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", url.strip())
    if not m:
        raise GitHubError("That doesn't look like a GitHub repository URL.")
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _raise_for_github(resp: httpx.Response, owner: str, repo: str) -> None:
    if resp.status_code == 404:
        raise GitHubError(
            f"Repository '{owner}/{repo}' was not found, or it is private."
        )
    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        raise GitHubError(
            "GitHub API rate limit reached. Try again later, or set GITHUB_TOKEN."
        )
    if resp.status_code >= 400:
        raise GitHubError(f"GitHub returned an error ({resp.status_code}).")


async def _fetch_readme(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/readme")
    if resp.status_code != 200:
        return ""
    try:
        text = base64.b64decode(resp.json().get("content", "")).decode(
            "utf-8", errors="ignore"
        )
    except Exception:
        return ""
    return text[:README_MAX_CHARS]


async def _fetch_languages(
    client: httpx.AsyncClient, owner: str, repo: str
) -> list[str]:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages")
    return list(resp.json().keys()) if resp.status_code == 200 else []


async def _fetch_root_files(
    client: httpx.AsyncClient, owner: str, repo: str
) -> list[str]:
    resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents")
    if resp.status_code != 200:
        return []
    return [item["name"] for item in resp.json() if isinstance(item, dict)]


async def fetch_repo_context(url: str) -> RepoContext:
    """Fetch metadata, README, languages and file list for a GitHub repo."""
    owner, repo = parse_repo_url(url)

    async with httpx.AsyncClient(timeout=20, headers=_headers()) as client:
        meta_resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
        _raise_for_github(meta_resp, owner, repo)
        meta = meta_resp.json()

        readme = await _fetch_readme(client, owner, repo)
        languages = await _fetch_languages(client, owner, repo)
        files = await _fetch_root_files(client, owner, repo)

    version = str(meta.get("pushed_at") or meta.get("updated_at") or "")
    return RepoContext(
        owner=owner,
        repo=repo,
        version=version,
        description=meta.get("description"),
        topics=meta.get("topics") or [],
        languages=languages,
        file_list=files,
        readme=readme,
        stars=meta.get("stargazers_count", 0),
    )

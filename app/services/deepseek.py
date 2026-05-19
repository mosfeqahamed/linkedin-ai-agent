import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.github import RepoContext

SYSTEM_PROMPT = """You are an expert LinkedIn content writer.

Write a single LinkedIn post based on the topic and optional description provided by the user.

Guidelines:
- Tone: professional but conversational, first-person where natural.
- Length: 800–1500 characters. Never exceed 3000 characters (LinkedIn's hard limit).
- Structure: open with a hook on the first line, then short paragraphs separated by blank lines.
- No clickbait, no excessive emojis (at most 1–2 if they fit naturally), no "Thoughts?" filler endings.
- Hashtags: 0–3 at the very end, only if they meaningfully help discovery.
- Output ONLY the post body. Do not include any preamble like "Here is your post:" or wrap it in quotes or code fences.
"""


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _client


ANALYZER_SYSTEM_PROMPT = """You are a senior software engineer analyzing a GitHub repository.

Given the repository's README, metadata, languages and file list, produce a concise
structured analysis.

Respond with ONLY a JSON object — no markdown, no commentary — with exactly these keys:
{
  "summary": "2-4 sentence plain-English summary of what the project does",
  "tech_stack": ["notable languages, frameworks and tools actually used"],
  "key_features": ["concrete capabilities the project provides"],
  "learning_modules": ["specific skills or concepts demonstrated by building this"]
}

For "learning_modules", name concrete technical skills — for example
"JWT authentication", "async MongoDB modeling with Beanie", or
"OAuth2 authorization-code flow".

Keep each list to at most 8 short, specific items. If information is missing,
infer conservatively from what is given."""


async def generate_post(
    topic: str,
    description: str | None = None,
    repo_analysis: dict | None = None,
    learning_modules: list[str] | None = None,
) -> str:
    """Generate a LinkedIn post.

    When `repo_analysis` is supplied (the output of `analyze_repo`), the post is
    grounded in the project's real features and learnings. `learning_modules`,
    if given, narrows which learnings the post should emphasise.
    """
    settings = get_settings()
    client = get_client()

    user_content = f"Topic: {topic}"
    if description:
        user_content += f"\n\nAdditional context:\n{description}"

    if repo_analysis:
        modules = learning_modules or repo_analysis.get("learning_modules", [])
        user_content += (
            "\n\nThis post is about a GitHub project the author built. Use the "
            "analysis below to keep the post concrete and credible — reference "
            "real features and what was learned; do not invent details.\n"
            f"Project summary: {repo_analysis.get('summary', '')}\n"
            f"Tech stack: {', '.join(repo_analysis.get('tech_stack', []))}\n"
            f"Key features: {', '.join(repo_analysis.get('key_features', []))}\n"
        )
        if modules:
            user_content += f"Emphasise these learnings: {', '.join(modules)}\n"

    resp = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=1.3,
        max_tokens=1200,
    )

    text = resp.choices[0].message.content
    if not text:
        raise RuntimeError("DeepSeek returned empty response")
    return text.strip()


async def analyze_repo(context: RepoContext) -> dict:
    """Stage 1 of the GitHub pipeline: structured analysis of a repository."""
    settings = get_settings()
    client = get_client()

    user_content = (
        f"Repository: {context.owner}/{context.repo}\n"
        f"Description: {context.description or '(none)'}\n"
        f"Topics: {', '.join(context.topics) or '(none)'}\n"
        f"Languages: {', '.join(context.languages) or '(unknown)'}\n"
        f"Root files: {', '.join(context.file_list) or '(unknown)'}\n\n"
        f"README:\n{context.readme or '(no README provided)'}"
    )

    resp = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=900,
    )

    raw = resp.choices[0].message.content
    if not raw:
        raise RuntimeError("Repo analysis returned an empty response")
    data = json.loads(raw)

    def _str_list(value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(x).strip() for x in value if str(x).strip()][:8]

    return {
        "summary": str(data.get("summary", "")).strip(),
        "tech_stack": _str_list(data.get("tech_stack")),
        "key_features": _str_list(data.get("key_features")),
        "learning_modules": _str_list(data.get("learning_modules")),
    }

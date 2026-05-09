from openai import AsyncOpenAI

from app.config import get_settings


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


async def generate_post(topic: str, description: str | None = None) -> str:
    settings = get_settings()
    client = get_client()

    user_content = f"Topic: {topic}"
    if description:
        user_content += f"\n\nAdditional context:\n{description}"

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

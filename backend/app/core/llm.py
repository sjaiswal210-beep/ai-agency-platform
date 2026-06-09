import httpx
import asyncio
from app.core.config import get_settings


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def _call_gemini(contents: list, api_key: str) -> str:
    """Try Gemini API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json={"contents": contents},
            timeout=120,
        )
        if resp.status_code == 429:
            raise Exception("RATE_LIMITED")
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def _call_groq(messages: list[dict], api_key: str) -> str:
    """Try Groq API (free Llama 3)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GROQ_API_URL,
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def chat_completion(messages: list[dict], model: str | None = None) -> str:
    """Call LLM - tries Gemini first, falls back to Groq if rate limited."""
    settings = get_settings()

    # Convert to Gemini format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # Try Gemini first
    if settings.gemini_api_key:
        try:
            return await _call_gemini(contents, settings.gemini_api_key)
        except Exception as e:
            if "RATE_LIMITED" in str(e) or "429" in str(e):
                pass  # Fall through to Groq
            else:
                # Try once more after short wait
                await asyncio.sleep(3)
                try:
                    return await _call_gemini(contents, settings.gemini_api_key)
                except Exception:
                    pass  # Fall through to Groq

    # Fallback to Groq
    groq_key = getattr(settings, 'groq_api_key', '') or ''
    if groq_key:
        try:
            return await _call_groq(messages, groq_key)
        except Exception as e:
            raise Exception(f"Both Gemini and Groq failed. Groq error: {str(e)[:100]}")

    raise Exception("LLM unavailable - Gemini rate limited and no Groq API key configured. Set GROQ_API_KEY env var.")

import httpx
import asyncio
from app.core.config import get_settings


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"


async def chat_completion(messages: list[dict], model: str | None = None) -> str:
    """Call Google Gemini API with automatic retry on rate limits."""
    settings = get_settings()

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    max_retries = 3
    for attempt in range(max_retries):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={settings.gemini_api_key}",
                json={"contents": contents},
                timeout=120,
            )
            
            if resp.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (attempt + 1) * 5  # 15s, 30s, 45s
                await asyncio.sleep(wait_time)
                continue
            
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    raise Exception("Gemini API rate limit exceeded after retries. Please wait a minute and try again.")

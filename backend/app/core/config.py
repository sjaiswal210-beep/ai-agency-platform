from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: str = ""
    gemini_api_key: str = ""
    google_places_key: str = ""
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    freellmapi_url: str = ""
    freellmapi_key: str = ""
    hf_token: str = ""
    openrouter_model: str = "gemini-2.5-flash-lite"
    redis_url: str = "redis://localhost:6379/0"
    api_secret_key: str = "dev-secret"
    n8n_webhook_url: str = "http://localhost:5678"
    n8n_api_key: str = ""
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

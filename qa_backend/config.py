from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql://neondb_owner:npg_RnjMpJ4DsKY7@ep-icy-tree-af8719ti.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
    redis_url: str = "redis://localhost:6379/0"
    google_application_credentials: str = ""
    gcs_bucket_name: str = "dietician-qa-audio"
    gemini_api_key: str = ""
    llm_provider: str = "gemini"
    transcription_provider: str = "google_stt"
    celery_concurrency: int = 10
    environment: str = "development"

    class Config:
        case_sensitive = False
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()

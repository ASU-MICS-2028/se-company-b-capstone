from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-only-insecure-secret"


class Settings(BaseSettings):
    """Read from env vars (or backend/.env). See .env.example."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./autocare.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    # Signs access tokens. MUST be set (long random string) outside dev/test.
    secret_key: str = DEV_SECRET
    token_ttl_minutes: int = 12 * 60

    @model_validator(mode="after")
    def _real_secret_outside_dev(self):
        if self.app_env not in ("dev", "test") and self.secret_key == DEV_SECRET:
            raise ValueError("SECRET_KEY must be set when APP_ENV is not dev/test")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

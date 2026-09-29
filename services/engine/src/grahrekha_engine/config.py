"""Engine settings, read from environment variables prefixed with ENGINE_."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ENGINE_")

    # Shared secret the web API layer sends in X-Engine-Secret.
    shared_secret: str

    @field_validator("shared_secret")
    @classmethod
    def _require_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("shared_secret must be a non-empty string")
        return value

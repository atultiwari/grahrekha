"""Engine settings, read from environment variables prefixed with ENGINE_."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ENGINE_")

    # Shared secret the web API layer sends in X-Engine-Secret.
    shared_secret: str
    # Downloaded model weights (scripts/fetch-data.sh --only M1,M2).
    models_dir: Path = Path(__file__).resolve().parents[2] / "models" / "weights"

    @field_validator("shared_secret")
    @classmethod
    def _require_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("shared_secret must be a non-empty string")
        return value

"""Engine settings, read from environment variables prefixed with ENGINE_."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_rules_dir() -> Path:
    """<repo>/rules when running from a checkout; ./rules otherwise (e.g. a container)."""
    parents = Path(__file__).resolve().parents
    return parents[4] / "rules" if len(parents) > 4 else Path("rules")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ENGINE_")

    # Shared secret the web API layer sends in X-Engine-Secret.
    shared_secret: str
    # Downloaded model weights (scripts/fetch-data.sh --only M1,M2).
    models_dir: Path = Path(__file__).resolve().parents[2] / "models" / "weights"
    # Interpretation rule base (repository rules/, CC BY 4.0). In containers, mount it
    # and set ENGINE_RULES_DIR (docker-compose.yml does).
    rules_dir: Path = Field(default_factory=lambda: _repo_rules_dir())

    @field_validator("shared_secret")
    @classmethod
    def _require_secret(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("shared_secret must be a non-empty string")
        return value

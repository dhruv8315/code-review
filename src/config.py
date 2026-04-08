"""
Configuration management.

Loads settings from environment variables or a .env file.
Precedence: CLI flags > environment variables > .env file > defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from models import Severity

def _find_dotenv() -> Path | None:
    """Walk up from cwd looking for a .env file."""
    cwd = Path.cwd()
    for directory in [cwd, *cwd.parents]:
        candidate = directory / ".env"
        if candidate.exists():
            return candidate
    return None

class Settings(BaseSettings):
    """
    All runtime settings for the reviewer.

    Automatically reads from environment variables (case-insensitive).
    Variable names map 1-to-1: GITHUB_TOKEN -> github_token, etc.
    """

    model_config = SettingsConfigDict(
        env_file=_find_dotenv(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ignore unknown env vars
    )

    # Required
    github_token: str           = Field(..., description="GitHub personal access token")
    #anthropic_api_key: str      = Field(..., description="Anthropic API key")

    # AI model settings
    model: str                  = Field(
        default="claude-sonnet-4",
        description="Anthropic model to use for reviews"
    )
    max_tokens: int             = Field(default=4096)
    context_lines: int          = Field(
        default=10,
        description="Number of surrounding unchanged lines to send as context"
    )

    # Behaviour
    fail_on_severity: Severity  = Field(
        default=Severity.CRITICAL,
        description="Exit non-zero if any issue at this severity or above is found"
    )
    post_comments: bool         = Field(
        default=True,
        description="Post inline review comments to the GitHub PR"
    )
    verbose: bool               = Field(default=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The cache means we only parse env/dotenv once per process. Call
    get_settings.cache_clear() in tests to reset between test cases.
    """
    return Settings()  # type: ignore[call-arg]
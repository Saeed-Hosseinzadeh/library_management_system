"""
Application configuration for the Library Management System.

This module centralizes runtime settings such as the database URL,
debug mode, logging preferences, and environment-specific behavior.

The configuration is loaded from environment variables and can also
optionally read a local `.env` file when `python-dotenv` is installed.

Example:
    DATABASE_URL=sqlite:///library.db
    APP_ENV=development
    DEBUG=true
    LOG_LEVEL=INFO
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv_if_available() -> None:
    """Load environment variables from a `.env` file if supported.

    This function attempts to import and execute `load_dotenv` from the
    `python-dotenv` package. If the package is not installed, it silently
    continues without failing.

    This design keeps the project flexible:
    - development environments can use `.env`
    - production environments can rely on real environment variables

    Returns:
        None
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return

    env_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


_load_dotenv_if_available()


def _get_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable safely.

    Accepted truthy values:
        - "1"
        - "true"
        - "yes"
        - "on"

    Accepted falsy values:
        - "0"
        - "false"
        - "no"
        - "off"

    Args:
        name: The environment variable name.
        default: The fallback value when the variable is not set.

    Returns:
        The parsed boolean value.

    Raises:
        ValueError: If the variable exists but contains an invalid boolean value.
    """
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"Invalid boolean value for environment variable '{name}': {raw_value!r}"
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings container.

    Attributes:
        app_name: Human-readable application name.
        app_env: Runtime environment, such as development or production.
        debug: Whether debug behavior is enabled.
        log_level: Logging level name.
        database_url: SQLAlchemy-compatible database connection URL.
        database_echo: Whether SQLAlchemy should echo generated SQL.
    """

    app_name: str
    app_env: str
    debug: bool
    log_level: str
    database_url: str
    database_echo: bool

    @property
    def is_development(self) -> bool:
        """Return whether the application runs in development mode."""
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Return whether the application runs in production mode."""
        return self.app_env.lower() == "production"


def _build_default_sqlite_url() -> str:
    """Build the default SQLite database URL.

    Returns:
        A SQLAlchemy-compatible SQLite database URL.
    """
    db_path = BASE_DIR / "library.db"
    return f"sqlite:///{db_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings.

    This function should be used as the single source of truth for
    application configuration.

    Returns:
        A validated `Settings` instance.
    """
    app_name = os.getenv("APP_NAME", "Library Management System")
    app_env = os.getenv("APP_ENV", "development").strip()
    debug = _get_bool_env("DEBUG", default=False)
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    database_url = os.getenv("DATABASE_URL", _build_default_sqlite_url()).strip()
    database_echo = _get_bool_env("DATABASE_ECHO", default=False)

    if not database_url:
        raise ValueError("DATABASE_URL must not be empty.")

    return Settings(
        app_name=app_name,
        app_env=app_env,
        debug=debug,
        log_level=log_level,
        database_url=database_url,
        database_echo=database_echo,
    )

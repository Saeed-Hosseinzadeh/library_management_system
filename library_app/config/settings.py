from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_FILE = BASE_DIR / "library.db"
LOG_FILE = BASE_DIR / "library.log"


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = f"sqlite:///{DB_FILE}"
    log_file: str = str(LOG_FILE)
    debug: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()

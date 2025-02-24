from dynaconf import settings as dynaconf_settings
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Dict

# Remove duplicate settings
dynaconf_settings.configure(
    ENVVAR_PREFIX="DYNACONF",
    SETTINGS_FILE_FOR_DYNACONF=[
        "settings.toml",
        ".secrets.toml",
        ".env",
    ],
)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Search and Scraping API"
    VERSION: str = "1.0.0"
    API_TOKEN: str = Field(default="test-token", env="API_TOKEN")
    # MongoDB settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    MONGODB_DB: str = Field(default="search_db", env="MONGODB_DB")
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost", env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")
    # Search settings
    SEARCH_RESULTS_LIMIT: int = Field(default=20, env="SEARCH_RESULTS_LIMIT")
    SCRAPE_LIMIT: int = Field(default=2, env="SCRAPE_LIMIT")
    MIN_SCORE_THRESHOLD: float = Field(default=0, env="MIN_SCORE_THRESHOLD")
    SEARCH_RATE_LIMIT: int = Field(default=20, env="SEARCH_RATE_LIMIT")
    JINA_RATE_LIMIT: int = Field(default=10, env="JINA_RATE_LIMIT")
    # Optional Jina settings
    JINA_API_KEY: str | None = Field(default=None, env="JINA_API_KEY")
    JINA_BASE_URL: str | None = Field(default=None, env="JINA_BASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # This will ignore extra fields in .env

    async def get_search_settings(self) -> Dict:
        """Get settings with DB overrides"""
        from .models.settings import SearchSettings

        db_settings = await SearchSettings.get_settings()
        return {
            "SEARCH_RESULTS_LIMIT": db_settings.searchResultsLimit,
            "SCRAPE_LIMIT": db_settings.scrapeLimit,
            "MIN_SCORE_THRESHOLD": db_settings.minScoreThreshold,
            "SEARCH_RATE_LIMIT": db_settings.searchRateLimit,
            "JINA_RATE_LIMIT": db_settings.jinaRateLimit,
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

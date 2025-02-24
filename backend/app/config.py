from dynaconf import settings as dynaconf_settings
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

# This is a simpler way to use dynaconf initially
dynaconf_settings.configure(
    ENVVAR_PREFIX="DYNACONF",
    SETTINGS_FILE_FOR_DYNACONF=[
        "settings.toml",
        ".secrets.toml",
        ".env",
    ],
)

# Add this for debugging
if __name__ == "__main__":
    print("Settings loaded:", dynaconf_settings.as_dict())

# Add search-related settings
dynaconf_settings.setdefault("SEARCH_RESULTS_LIMIT", 20)  # Maximum search results to fetch
dynaconf_settings.setdefault("SCRAPE_LIMIT", 2)  # Maximum URLs to scrape
dynaconf_settings.setdefault("MIN_SCORE_THRESHOLD", 0.2)  # Minimum relevance score

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="Search API", env="PROJECT_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    API_TOKEN: str = Field(default="test-token", env="API_TOKEN")
    
    # MongoDB settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    DATABASE_NAME: str = Field(default="search_db", env="DATABASE_NAME")
    MONGODB_DB: str = Field(default="scraping_db", env="MONGODB_DB")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost", env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")
    
    # Search settings
    MAX_RESULTS_PER_QUERY: int = Field(default=10, env="MAX_RESULTS_PER_QUERY")
    SEARCH_RESULTS_LIMIT: int = Field(default=2, env="SEARCH_RESULTS_LIMIT")
    SCRAPE_LIMIT: int = Field(default=2, env="SCRAPE_LIMIT")
    MIN_SCORE_THRESHOLD: float = Field(default=0.2, env="MIN_SCORE_THRESHOLD")
    MAX_SEARCH_RESULTS: int = Field(default=8, env="MAX_SEARCH_RESULTS")
    
    # Optional Jina settings
    JINA_API_KEY: str | None = Field(default=None, env="JINA_API_KEY")
    JINA_BASE_URL: str | None = Field(default=None, env="JINA_BASE_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # This will ignore extra fields in .env

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create a single instance of settings
settings = get_settings()

# Export all settings
__all__ = ["settings"]

# For debugging
if __name__ == "__main__":
    print("Settings loaded:", settings.model_dump())

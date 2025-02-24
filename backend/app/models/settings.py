from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SearchSettings(BaseModel):
    maxResultsPerQuery: int = 10
    searchResultsLimit: int = 2
    scrapeLimit: int = 2
    minScoreThreshold: float = 0.2
    jinaRateLimit: int = 20
    searchRateLimit: int = 20
    updated_at: Optional[datetime] = None

class Settings:
    collection_name = "settings"

    @classmethod
    async def get_settings(cls, db) -> SearchSettings:
        """Get current settings or create with defaults"""
        settings_doc = await db.db[cls.collection_name].find_one({})
        if not settings_doc:
            settings = SearchSettings()
            settings.updated_at = datetime.utcnow()
            await db.db[cls.collection_name].insert_one(settings.dict())
            return settings
        return SearchSettings(**settings_doc)

    @classmethod
    async def update_settings(cls, db, settings: SearchSettings):
        """Update settings"""
        settings.updated_at = datetime.utcnow()
        await db.db[cls.collection_name].update_one(
            {}, 
            {"$set": settings.dict()}, 
            upsert=True
        ) 
from pydantic import BaseModel
from typing import Dict
from ..db import db


class SearchSettings(BaseModel):
    maxResultsPerQuery: int = 20
    searchResultsLimit: int = 20
    scrapeLimit: int = 2
    minScoreThreshold: float = 0
    searchRateLimit: int = 20
    jinaRateLimit: int = 10

    @classmethod
    async def get_settings(cls) -> "SearchSettings":
        """Get settings from DB, falling back to defaults"""
        try:
            settings_doc = await db.db.settings.find_one({})
            if settings_doc:
                return cls(**settings_doc)
        except Exception:
            pass
        return cls()

    @classmethod
    async def update_settings(cls, settings_dict: Dict):
        """Update settings in DB"""
        await db.db.settings.replace_one({}, settings_dict, upsert=True)

from pydantic import BaseModel
from typing import Dict, List
from ..db import db
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)


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


class WhitelistDomain:
    @classmethod
    async def get_all_domains(cls) -> List[str]:
        """Get all whitelist domains from DB"""
        try:
            # Debug log
            logger.info("Fetching whitelist domains...")

            # Get the document containing the urls array
            doc = await db.db.whitelist.find_one({})
            logger.info(f"Found whitelist document: {doc}")

            if doc and "urls" in doc:
                # Extract and clean URLs
                domains = [
                    url.replace("https://", "").replace("http://", "").strip("/")
                    for url in doc["urls"]
                    if url
                ]
                logger.info(f"Extracted whitelist domains: {domains}")
                return domains

            logger.warning("No whitelist URLs found in database")
            return []

        except Exception as e:
            logger.error(f"Error fetching whitelist domains: {e}")
            return []

    @classmethod
    async def add_domain(cls, domain: str) -> bool:
        """Add a domain to whitelist"""
        try:
            # Clean the domain
            clean_domain = (
                domain.replace("https://", "").replace("http://", "").strip("/")
            )

            # Get existing document or create new one
            doc = await db.db.whitelist.find_one({})
            if doc:
                # Add to existing urls array if not already present
                if "urls" not in doc:
                    doc["urls"] = []
                if clean_domain not in doc["urls"]:
                    result = await db.db.whitelist.update_one(
                        {"_id": doc["_id"]}, {"$addToSet": {"urls": clean_domain}}
                    )
                    success = result.modified_count > 0
                else:
                    success = True  # Already exists
            else:
                # Create new document with urls array
                result = await db.db.whitelist.insert_one({"urls": [clean_domain]})
                success = bool(result.inserted_id)

            if success:
                logger.info(f"Successfully added domain to whitelist: {clean_domain}")
            return success

        except Exception as e:
            logger.error(f"Error adding whitelist domain: {e}")
            return False

    @classmethod
    async def remove_domain(cls, domain: str) -> bool:
        """Remove a domain from whitelist"""
        try:
            # Clean the domain
            clean_domain = (
                domain.replace("https://", "").replace("http://", "").strip("/")
            )

            # Remove from urls array
            result = await db.db.whitelist.update_one(
                {}, {"$pull": {"urls": clean_domain}}
            )

            success = result.modified_count > 0
            if success:
                logger.info(
                    f"Successfully removed domain from whitelist: {clean_domain}"
                )
            else:
                logger.warning(f"Domain not found in whitelist: {clean_domain}")
            return success

        except Exception as e:
            logger.error(f"Error removing whitelist domain: {e}")
            return False

    @classmethod
    async def check_db_state(cls) -> Dict:
        """Debug function to check database state"""
        try:
            whitelist_count = await db.db.whitelist.count_documents({})
            blacklist_count = await db.db.blacklist.count_documents({})

            whitelist_sample = (
                await db.db.whitelist.find().limit(5).to_list(length=None)
            )
            blacklist_sample = (
                await db.db.blacklist.find().limit(5).to_list(length=None)
            )

            collections = await db.db.list_collection_names()

            state = {
                "collections": collections,
                "whitelist_count": whitelist_count,
                "blacklist_count": blacklist_count,
                "whitelist_sample": whitelist_sample,
                "blacklist_sample": blacklist_sample,
            }

            logger.info(f"Database state: {state}")
            return state

        except Exception as e:
            logger.error(f"Error checking database state: {e}")
            return {}


class BlacklistDomain:
    @classmethod
    async def get_all_domains(cls) -> List[str]:
        """Get all blacklist domains from DB"""
        try:
            # Debug log
            logger.info("Fetching blacklist domains...")

            # Get the document containing the urls array
            doc = await db.db.blacklist.find_one({})
            logger.info(f"Found blacklist document: {doc}")

            if doc and "urls" in doc:
                # Extract and clean URLs
                domains = [
                    url.replace("https://", "").replace("http://", "").strip("/")
                    for url in doc["urls"]
                    if url
                ]
                logger.info(f"Extracted blacklist domains: {domains}")
                return domains

            logger.warning("No blacklist URLs found in database")
            return []

        except Exception as e:
            logger.error(f"Error fetching blacklist domains: {e}")
            return []

    @classmethod
    async def add_domain(cls, domain: str) -> bool:
        """Add a domain to blacklist"""
        try:
            # Clean the domain
            clean_domain = (
                domain.replace("https://", "").replace("http://", "").strip("/")
            )

            # Get existing document or create new one
            doc = await db.db.blacklist.find_one({})
            if doc:
                # Add to existing urls array if not already present
                if "urls" not in doc:
                    doc["urls"] = []
                if clean_domain not in doc["urls"]:
                    result = await db.db.blacklist.update_one(
                        {"_id": doc["_id"]}, {"$addToSet": {"urls": clean_domain}}
                    )
                    success = result.modified_count > 0
                else:
                    success = True  # Already exists
            else:
                # Create new document with urls array
                result = await db.db.blacklist.insert_one({"urls": [clean_domain]})
                success = bool(result.inserted_id)

            if success:
                logger.info(f"Successfully added domain to blacklist: {clean_domain}")
            return success

        except Exception as e:
            logger.error(f"Error adding blacklist domain: {e}")
            return False

    @classmethod
    async def remove_domain(cls, domain: str) -> bool:
        """Remove a domain from blacklist"""
        try:
            # Clean the domain
            clean_domain = (
                domain.replace("https://", "").replace("http://", "").strip("/")
            )

            # Remove from urls array
            result = await db.db.blacklist.update_one(
                {}, {"$pull": {"urls": clean_domain}}
            )

            success = result.modified_count > 0
            if success:
                logger.info(
                    f"Successfully removed domain from blacklist: {clean_domain}"
                )
            else:
                logger.warning(f"Domain not found in blacklist: {clean_domain}")
            return success

        except Exception as e:
            logger.error(f"Error removing blacklist domain: {e}")
            return False

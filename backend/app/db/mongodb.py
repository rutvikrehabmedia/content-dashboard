import motor.motor_asyncio
from ..config import settings
import logging
from bson import ObjectId
import json
from typing import Dict

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def _serialize_doc(self, doc):
        """Convert MongoDB document to JSON-serializable format"""
        if doc is None:
            return None

        if isinstance(doc, dict):
            for k, v in doc.items():
                if isinstance(v, ObjectId):
                    doc[k] = str(v)
                elif isinstance(v, dict):
                    doc[k] = self._serialize_doc(v)
                elif isinstance(v, list):
                    doc[k] = [self._serialize_doc(item) for item in v]
            return doc
        elif isinstance(doc, list):
            return [self._serialize_doc(item) for item in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        return doc

    async def connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.MONGODB_DB]
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    async def get_db_stats(self):
        """Get database statistics"""
        try:
            return await self.db.command("dbStats")
        except Exception as e:
            logger.error(f"Error getting DB stats: {e}")
            return {"error": str(e)}

    async def ensure_db(self):
        """Ensure database connection"""
        if not self.db:
            await self.connect()
        return self.db

    async def log_search(self, log_data: Dict):
        """Log search data to MongoDB"""
        try:
            if log_data.get("_replace"):
                del log_data["_replace"]
            await self.db.logs.replace_one(
                {"process_id": log_data["process_id"]}, log_data, upsert=True
            )
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            raise

    async def get_logs(self, skip=0, limit=50, sort=None):
        """Get logs with pagination and sorting"""
        collection = self.db.logs
        cursor = collection.find({})

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.skip(skip).limit(limit)
        logs = await cursor.to_list(length=None)
        return [self._serialize_doc(log) for log in logs]

    async def count_logs(self):
        """Get total count of logs"""
        return await self.db.logs.count_documents({})

    async def store_scraped_content(self, **kwargs):
        """Store scraped content"""
        collection = self.db.scraped_content
        result = await collection.insert_one(kwargs)
        return result.inserted_id

    async def get_whitelist(self) -> dict:
        """Get whitelist URLs"""
        try:
            doc = await self.db.whitelist.find_one({})
            return {"urls": doc.get("urls", []) if doc else []}
        except Exception as e:
            logger.error(f"Error getting whitelist: {e}")
            return {"urls": []}

    async def get_blacklist(self) -> dict:
        """Get blacklist URLs"""
        try:
            doc = await self.db.blacklist.find_one({})
            return {"urls": doc.get("urls", []) if doc else []}
        except Exception as e:
            logger.error(f"Error getting blacklist: {e}")
            return {"urls": []}

    async def update_whitelist(self, urls: list) -> dict:
        """Update whitelist URLs"""
        try:
            await self.db.whitelist.update_one(
                {}, {"$set": {"urls": urls}}, upsert=True
            )
            return {"urls": urls}
        except Exception as e:
            logger.error(f"Error updating whitelist: {e}")
            raise

    async def update_blacklist(self, urls: list) -> dict:
        """Update blacklist URLs"""
        try:
            await self.db.blacklist.update_one(
                {}, {"$set": {"urls": urls}}, upsert=True
            )
            return {"urls": urls}
        except Exception as e:
            logger.error(f"Error updating blacklist: {e}")
            raise


db = MongoDB()

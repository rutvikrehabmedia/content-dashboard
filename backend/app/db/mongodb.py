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
        """Create database connection"""
        try:
            if self.client is None:
                self.client = motor.motor_asyncio.AsyncIOMotorClient(
                    settings.MONGODB_URL
                )
                self.db = self.client[settings.MONGODB_DB]
                # Test connection
                await self.client.server_info()
                logger.info("Connected to MongoDB")
                return self.db
        except Exception as e:
            self.client = None
            self.db = None
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
        try:
            if self.db is None:
                await self.connect()
                # Initialize collections after connection
                await self.initialize_collections()
            return self.db
        except Exception as e:
            logger.error(f"Error ensuring database connection: {e}")
            raise

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

    async def log_scrape(self, log_data: Dict):
        """Log scrape data to MongoDB"""
        try:
            await self.ensure_db()
            if log_data.get("_replace"):
                del log_data["_replace"]
                await self.db.scrape_logs.replace_one(
                    {"process_id": log_data["process_id"]}, log_data, upsert=True
                )
            else:
                await self.db.scrape_logs.insert_one(log_data)
        except Exception as e:
            logger.error(f"Error logging scrape: {e}")
            raise

    async def get_scrape_logs(self, skip=0, limit=50, sort=None):
        """Get scrape logs with pagination and sorting"""
        try:
            db = await self.ensure_db()
            if db is None:
                raise Exception("Database connection not available")

            cursor = db.scrape_logs.find({})

            if sort:
                cursor = cursor.sort(sort)

            cursor = cursor.skip(skip).limit(limit)
            logs = await cursor.to_list(length=None)
            return [self._serialize_doc(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting scrape logs: {e}")
            raise

    async def count_scrape_logs(self):
        """Get total count of scrape logs"""
        try:
            await self.ensure_db()
            return await self.db.scrape_logs.count_documents({})
        except Exception as e:
            logger.error(f"Error counting scrape logs: {e}")
            raise

    async def initialize_collections(self):
        """Initialize required collections"""
        try:
            collections = ["logs", "scrape_logs", "whitelist", "blacklist"]
            for collection in collections:
                try:
                    await self.db[collection].insert_one({"_id": "init"})
                    await self.db[collection].delete_one({"_id": "init"})
                    logger.info(f"Initialized collection: {collection}")
                except Exception as e:
                    logger.error(f"Error initializing collection {collection}: {e}")
        except Exception as e:
            logger.error(f"Error in initialize_collections: {e}")
            raise


db = MongoDB()

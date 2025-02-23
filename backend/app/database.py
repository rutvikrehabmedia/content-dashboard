from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
import asyncio
from .config import settings
import urllib.parse
import backoff  # Add this to requirements.txt

logger = logging.getLogger(__name__)

class MongoManager:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    def get_connection_url(cls) -> str:
        """Build MongoDB connection URL from settings."""
        if settings.MONGODB_URL.startswith("mongodb+srv"):
            # Using MongoDB Atlas
            username = urllib.parse.quote_plus(settings.MONGODB_USER)
            password = urllib.parse.quote_plus(settings.MONGODB_PASS)
            cluster = settings.MONGODB_CLUSTER
            return f"mongodb+srv://{username}:{password}@{cluster}.mongodb.net"
        return settings.MONGODB_URL

    @classmethod
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=30
    )
    async def connect_to_database(cls, mongodb_url: Optional[str] = None):
        """Create database connection."""
        try:
            logger.info(f"Connecting to MongoDB at: {mongodb_url}")
            url = mongodb_url or settings.MONGODB_URL
            
            cls.client = AsyncIOMotorClient(
                url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            
            # Test connection
            await cls.client.server_info()
            logger.info("Successfully connected to MongoDB server")
            
            # Initialize database
            cls.db = cls.client[settings.MONGODB_DB]
            logger.info(f"Using database: {settings.MONGODB_DB}")
            
            # Ensure collections exist
            await cls.db.whitelist.insert_one({"_id": "init"})
            await cls.db.whitelist.delete_one({"_id": "init"})
            
            await cls.db.blacklist.insert_one({"_id": "init"})
            await cls.db.blacklist.delete_one({"_id": "init"})
            
            await cls.create_indexes()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    @classmethod
    async def create_indexes(cls):
        """Create database indexes."""
        try:
            # Whitelist indexes
            await cls.db.whitelist.create_index("url", unique=True)
            await cls.db.whitelist.create_index("added_at")

            # Blacklist indexes
            await cls.db.blacklist.create_index("url", unique=True)
            await cls.db.blacklist.create_index("added_at")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    @classmethod
    async def close_database_connection(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            logger.info("Closed connection with MongoDB.")

    @classmethod
    async def get_db_stats(cls):
        """Get database statistics."""
        try:
            stats = await cls.db.command("dbStats")
            collections = await cls.db.list_collection_names()
            return {
                "database": settings.MONGODB_DB,
                "collections": collections,
                "stats": {
                    "objects": stats.get("objects", 0),
                    "collections": stats.get("collections", 0),
                    "dataSize": stats.get("dataSize", 0),
                    "storageSize": stats.get("storageSize", 0),
                }
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return None

mongodb = MongoManager() 
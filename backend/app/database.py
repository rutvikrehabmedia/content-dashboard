from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from .config import settings
import urllib.parse

logger = logging.getLogger(__name__)


class MongoManager:
    def __init__(self):
        self.client = None
        self.db = None
        self._connected = False

    def get_connection_url(self) -> str:
        """Build MongoDB connection URL from settings."""
        if settings.MONGODB_URL.startswith("mongodb+srv"):
            username = urllib.parse.quote_plus(settings.MONGODB_USER)
            password = urllib.parse.quote_plus(settings.MONGODB_PASS)
            cluster = settings.MONGODB_CLUSTER
            return f"mongodb+srv://{username}:{password}@{cluster}.mongodb.net"
        return settings.MONGODB_URL

    async def connect_to_database(self, mongodb_url: Optional[str] = None):
        """Create database connection."""
        try:
            if self._connected:
                logger.info("Using existing database connection")
                return self.db

            logger.info(f"Connecting to MongoDB at: {mongodb_url or 'default url'}")
            url = mongodb_url or self.get_connection_url()

            self.client = AsyncIOMotorClient(
                url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )

            # Test connection
            logger.info("Testing connection...")
            await self.client.server_info()
            logger.info("Successfully connected to MongoDB server")

            # Initialize database
            self.db = self.client[settings.MONGODB_DB]
            logger.info(f"Using database: {settings.MONGODB_DB}")

            # Initialize collections
            logger.info("Initializing collections...")
            await self._initialize_collections()
            await self._create_indexes()

            self._connected = True
            logger.info("Database initialization complete")
            return self.db

        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.client = None
            self.db = None
            self._connected = False
            raise

    async def _initialize_collections(self):
        """Initialize required collections."""
        collections = ["scrape_logs", "logs", "whitelist", "blacklist"]
        for collection in collections:
            try:
                await self.db[collection].insert_one({"_id": "init"})
                await self.db[collection].delete_one({"_id": "init"})
            except Exception as e:
                logger.error(f"Error initializing collection {collection}: {e}")

    async def _create_indexes(self):
        """Create necessary indexes."""
        try:
            # Logs indexes
            await self.db.logs.create_index("process_id")
            await self.db.logs.create_index("parent_process_id")
            await self.db.logs.create_index("timestamp")
            await self.db.logs.create_index([("type", 1), ("timestamp", -1)])

            # Scrape logs indexes
            await self.db.scrape_logs.create_index("process_id")
            await self.db.scrape_logs.create_index("timestamp")
            await self.db.scrape_logs.create_index([("type", 1), ("timestamp", -1)])

            # List indexes
            await self.db.whitelist.create_index("url", unique=True)
            await self.db.blacklist.create_index("url", unique=True)

            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    async def close_database_connection(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self._connected = False
            logger.info("Closed connection with MongoDB.")


mongodb = MongoManager()

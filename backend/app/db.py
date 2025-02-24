from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime
from .database import mongodb
from bson import ObjectId
import json
import uuid
from app.models import LogType, LogStatus, BaseLog, SearchLog, ScrapeLog

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None and mongodb.db is not None:
            self._db = mongodb.db
            logger.info("Database connection initialized")
        return self._db

    async def ensure_db(self):
        if self._db is None:
            logger.info("Initializing database connection...")
            await mongodb.connect_to_database()
            self._db = mongodb.db
            await self.create_indexes()  # Create indexes after connection
        if self._db is None:
            raise Exception("Failed to initialize database connection")
        return self._db

    async def store_scraped_content(self, **kwargs) -> bool:
        """Store scraped content with better handling."""
        try:
            db = await self.ensure_db()

            # Ensure required fields
            required_fields = ["id", "url", "content", "timestamp"]
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"Missing required field: {field}")

            # Add metadata if not present
            if "meta_data" not in kwargs:
                kwargs["meta_data"] = json.dumps(
                    {
                        "url": kwargs["url"],
                        "length": len(kwargs["content"]),
                        "timestamp": kwargs["timestamp"],
                    }
                )

            result = await db.scraped_content.update_one(
                {"url": kwargs["url"]}, {"$set": kwargs}, upsert=True
            )

            logger.info(f"Stored scraped content for URL: {kwargs['url']}")
            return True
        except Exception as e:
            logger.error(f"Error storing scraped content: {str(e)}")
            return False

    async def get_scraped_content(self) -> List[Dict]:
        try:
            db = await self.ensure_db()
            cursor = db.scraped_content.find().sort("timestamp", -1)
            results = await cursor.to_list(length=None)
            logger.info(f"Retrieved {len(results)} scraped content records")
            return results
        except Exception as e:
            logger.error(f"Error getting scraped content: {str(e)}")
            return []

    async def log_search(self, log_data: Dict[str, Any]) -> None:
        """Log a search operation with proper update handling."""
        try:
            # Convert enums to values if present
            if isinstance(log_data.get("type"), LogType):
                log_data["type"] = log_data["type"].value
            if isinstance(log_data.get("status"), LogStatus):
                log_data["status"] = log_data["status"].value

            # Ensure required fields
            if "process_id" not in log_data:
                raise ValueError("process_id is required for logging")

            # Add timestamp if not present
            if "timestamp" not in log_data:
                log_data["timestamp"] = datetime.utcnow()

            # Handle updates vs new entries
            existing_log = await self.db.logs.find_one(
                {"process_id": log_data["process_id"]}
            )

            if existing_log:
                # Update existing log
                update_data = {"$set": {}}

                # Update all provided fields
                for key, value in log_data.items():
                    if key != "_id":  # Don't update the _id field
                        update_data["$set"][key] = value

                await self.db.logs.update_one(
                    {"process_id": log_data["process_id"]}, update_data
                )
            else:
                # Insert new log
                await self.db.logs.insert_one(log_data)

            logger.info(
                f"Search log {'updated' if existing_log else 'created'} for process {log_data['process_id']}"
            )
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            raise

    async def count_logs(self) -> int:
        """Get total count of logs."""
        try:
            db = await self.ensure_db()
            return await db.logs.count_documents(
                {
                    "$or": [
                        {"parent_process_id": {"$exists": False}},
                        {"parent_process_id": None},
                    ]
                }
            )
        except Exception as e:
            logger.error(f"Error counting logs: {str(e)}")
            return 0

    async def get_logs(
        self, skip: int = 0, limit: int = 50, sort: List[Tuple[str, int]] = None
    ) -> List[dict]:
        """Get logs with pagination and sorting."""
        try:
            db = await self.ensure_db()

            # Get parent logs and logs without parents
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"parent_process_id": {"$exists": False}},
                            {"parent_process_id": None},
                        ]
                    }
                },
                {"$sort": {"timestamp": -1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "logs",
                        "localField": "process_id",
                        "foreignField": "parent_process_id",
                        "as": "child_logs",
                    }
                },
            ]

            cursor = db.logs.aggregate(pipeline)
            logs = []
            async for doc in cursor:
                formatted_doc = self.serialize_document(doc)
                if "child_logs" in formatted_doc:
                    formatted_doc["child_logs"] = sorted(
                        [
                            self.serialize_document(child)
                            for child in formatted_doc["child_logs"]
                        ],
                        key=lambda x: x.get("timestamp", ""),
                        reverse=True,
                    )
                logs.append(formatted_doc)

            return logs

        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}")
            raise

    def serialize_document(self, doc: Dict) -> Dict:
        """Serialize MongoDB document with proper handling of special types."""
        if isinstance(doc, dict):
            return {
                key: (
                    str(value)
                    if isinstance(value, ObjectId)
                    else (
                        value.isoformat()
                        if isinstance(value, datetime)
                        else (
                            self.serialize_document(value)
                            if isinstance(value, (dict, list))
                            else value
                        )
                    )
                )
                for key, value in doc.items()
            }
        elif isinstance(doc, list):
            return [self.serialize_document(item) for item in doc]
        return doc

    async def get_whitelist(self) -> List[str]:
        try:
            db = await self.ensure_db()
            cursor = db.whitelist.find({}, {"url": 1, "_id": 0})
            docs = await cursor.to_list(length=None)
            urls = [doc["url"] for doc in docs]
            logger.info(f"Retrieved {len(urls)} URLs from whitelist")
            return urls
        except Exception as e:
            logger.error(f"Error getting whitelist: {str(e)}")
            return []

    async def get_blacklist(self) -> List[str]:
        try:
            db = await self.ensure_db()
            cursor = db.blacklist.find({}, {"url": 1, "_id": 0})
            docs = await cursor.to_list(length=None)
            urls = [doc["url"] for doc in docs]
            logger.info(f"Retrieved {len(urls)} URLs from blacklist")
            return urls
        except Exception as e:
            logger.error(f"Error getting blacklist: {str(e)}")
            return []

    async def add_to_whitelist(self, urls: List[str]) -> bool:
        try:
            db = await self.ensure_db()
            logger.info(f"Adding URLs to whitelist: {urls}")

            # Filter out empty URLs
            valid_urls = [url for url in urls if url and url.strip()]
            if not valid_urls:
                raise ValueError("No valid URLs provided")

            # Insert each URL individually instead of bulk write
            for url in valid_urls:
                await db.whitelist.update_one(
                    {"url": url},
                    {"$set": {"url": url, "added_at": datetime.utcnow()}},
                    upsert=True,
                )

            logger.info(f"Successfully added {len(valid_urls)} URLs to whitelist")
            return True

        except Exception as e:
            logger.error(f"Error adding to whitelist: {str(e)}")
            raise

    async def add_to_blacklist(self, urls: List[str]) -> bool:
        try:
            db = await self.ensure_db()
            logger.info(f"Adding URLs to blacklist: {urls}")

            # Filter out empty URLs
            valid_urls = [url for url in urls if url and url.strip()]
            if not valid_urls:
                raise ValueError("No valid URLs provided")

            # Insert each URL individually
            for url in valid_urls:
                await db.blacklist.update_one(
                    {"url": url},
                    {"$set": {"url": url, "added_at": datetime.utcnow()}},
                    upsert=True,
                )

            logger.info(f"Successfully added {len(valid_urls)} URLs to blacklist")
            return True

        except Exception as e:
            logger.error(f"Error adding to blacklist: {str(e)}")
            raise

    async def update_whitelist(self, urls: List[str]) -> None:
        """Update the whitelist with new URLs."""
        try:
            # Clear existing whitelist and add new URLs (even if empty)
            await self.db.whitelist.delete_many({})
            if urls:  # Only insert if there are URLs
                await self.db.whitelist.insert_many([{"url": url} for url in urls])
            logger.info(f"Successfully updated whitelist with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"Error updating whitelist: {e}")
            raise

    async def update_blacklist(self, urls: List[str]) -> None:
        """Update the blacklist with new URLs."""
        try:
            # Clear existing blacklist and add new URLs (even if empty)
            await self.db.blacklist.delete_many({})
            if urls:  # Only insert if there are URLs
                await self.db.blacklist.insert_many([{"url": url} for url in urls])
            logger.info(f"Successfully updated blacklist with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"Error updating blacklist: {e}")
            raise

    async def cleanup_database(self) -> None:
        """Clean up all collections in the database."""
        try:
            db = await self.ensure_db()
            # Drop all collections
            await db.logs.drop()
            await db.search_logs.drop()
            await db.scrape_logs.drop()
            await db.whitelist.drop()
            await db.blacklist.drop()
            await db.scraped_content.drop()

            # Create indexes after cleanup
            await db.logs.create_index("process_id")
            await db.logs.create_index("parent_process_id")
            await db.logs.create_index("timestamp")
            await db.search_logs.create_index("process_id")
            await db.search_logs.create_index("timestamp")

            logger.info("Database cleaned successfully")
        except Exception as e:
            logger.error(f"Error cleaning database: {e}")
            raise

    async def create_indexes(self) -> None:
        """Create necessary indexes for the database."""
        try:
            db = await self.ensure_db()
            await db.logs.create_index("process_id")
            await db.logs.create_index("parent_process_id")
            await db.logs.create_index("timestamp")
            await db.logs.create_index([("type", 1), ("timestamp", -1)])
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise


db = Database()

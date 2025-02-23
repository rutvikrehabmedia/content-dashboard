from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
from .database import mongodb
from bson import ObjectId
import json
import uuid

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
                kwargs["meta_data"] = json.dumps({
                    "url": kwargs["url"],
                    "length": len(kwargs["content"]),
                    "timestamp": kwargs["timestamp"]
                })
                
            result = await db.scraped_content.update_one(
                {"url": kwargs["url"]},
                {"$set": kwargs},
                upsert=True
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

    async def log_search(self, **kwargs) -> bool:
        """Store search log with better error handling."""
        try:
            db = await self.ensure_db()
            
            # Ensure timestamp
            if "timestamp" not in kwargs:
                kwargs["timestamp"] = datetime.utcnow()
                
            # Convert any non-serializable objects to strings
            for key, value in kwargs.items():
                if isinstance(value, (dict, list)):
                    kwargs[key] = json.dumps(value)
                    
            # Ensure required fields
            if "query" not in kwargs:
                raise ValueError("Query is required for logging")
                
            if "process_id" not in kwargs:
                kwargs["process_id"] = str(uuid.uuid4())
                
            if "status" not in kwargs:
                kwargs["status"] = "started"
                
            result = await db.search_logs.insert_one(kwargs)
            logger.info(f"Search log created with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging search: {str(e)}")
            return False

    async def count_logs(self) -> int:
        """Get total count of logs."""
        try:
            db = await self.ensure_db()
            return await db.search_logs.count_documents({})
        except Exception as e:
            logger.error(f"Error counting logs: {str(e)}")
            return 0

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        sort: List[Tuple[str, int]] = None
    ) -> List[dict]:
        """Get logs with pagination and sorting."""
        try:
            db = await self.ensure_db()
            cursor = db.search_logs.find({})
            
            if sort:
                cursor = cursor.sort(sort)
            
            cursor = cursor.skip(skip).limit(limit)
            
            logs = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string and format timestamps
            formatted_logs = []
            for log in logs:
                formatted_log = dict(log)
                formatted_log['_id'] = str(log['_id'])
                
                # Parse stored JSON strings
                for field in ['results', 'whitelist', 'blacklist', 'metadata']:
                    if field in formatted_log and isinstance(formatted_log[field], str):
                        try:
                            formatted_log[field] = json.loads(formatted_log[field])
                        except:
                            pass
                
                formatted_logs.append(formatted_log)
            
            logger.info(f"Retrieved {len(formatted_logs)} logs")
            return formatted_logs
            
        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}")
            raise

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
                    {
                        "$set": {
                            "url": url,
                            "added_at": datetime.utcnow()
                        }
                    },
                    upsert=True
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
                    {
                        "$set": {
                            "url": url,
                            "added_at": datetime.utcnow()
                        }
                    },
                    upsert=True
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

db = Database() 
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from .scraper import WebScraper, enhanced_search
from .db import db

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self):
        self.scraper = WebScraper()
        self.active_processes = {}

    async def process_batch(
        self,
        queries: List[str],
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None
    ) -> str:
        process_id = str(uuid.uuid4())
        
        try:
            # Start processing in background
            asyncio.create_task(
                self._process_queries(
                    process_id=process_id,
                    queries=queries,
                    whitelist=whitelist,
                    blacklist=blacklist
                )
            )
            
            return process_id
            
        except Exception as e:
            logger.error(f"Error starting batch process: {str(e)}")
            raise

    async def _process_queries(
        self,
        process_id: str,
        queries: List[str],
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None
    ):
        try:
            self.active_processes[process_id] = {
                "status": "running",
                "total": len(queries),
                "completed": 0,
                "results": [],
                "errors": []
            }

            for query in queries:
                try:
                    urls = await enhanced_search(
                        query=query,
                        whitelist=whitelist,
                        blacklist=blacklist
                    )
                    
                    self.active_processes[process_id]["results"].append({
                        "query": query,
                        "urls": urls
                    })
                    self.active_processes[process_id]["completed"] += 1
                    
                except Exception as e:
                    self.active_processes[process_id]["errors"].append({
                        "query": query,
                        "error": str(e)
                    })

            self.active_processes[process_id]["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            self.active_processes[process_id]["status"] = "failed"
            self.active_processes[process_id]["error"] = str(e)

    def get_process_status(self, process_id: str) -> Dict:
        """Get the status of a batch process."""
        return self.active_processes.get(process_id, {
            "status": "not_found",
            "error": "Process ID not found"
        })

batch_processor = BatchProcessor() 
from fastapi import APIRouter, Depends, HTTPException, Header, status
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple
from .scraper import WebScraper, enhanced_search
from .config import settings
from .db import db
from .batch_processor import batch_processor
from .api import (
    SearchRequest,
    SearchResponse,
    ListResponse,
    UpdateListRequest,
    BatchRequest,
)
from app.models import LogType, LogStatus, BaseLog, SearchLog, ScrapeLog
import asyncio
from bson import ObjectId
from pydantic import BaseModel
import uuid
import math
from .services.search import perform_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
scraper = WebScraper()


# Add these models at the top with other models
class BulkSearchQuery(BaseModel):
    query: str
    whitelist: List[str] = []
    blacklist: List[str] = []


class BulkSearchRequest(BaseModel):
    queries: List[BulkSearchQuery]
    globalListsEnabled: bool = False
    globalWhitelist: List[str] = []
    globalBlacklist: List[str] = []


class SettingsUpdate(BaseModel):
    maxResultsPerQuery: int


async def verify_token(
    x_token: str = Header(..., description="API token for authentication")
):
    if x_token != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        )
    return x_token


# Add these logging helper functions
async def log_search_start(process_id: str, request: SearchRequest):
    """Log the start of a search request"""
    await db.log_search(
        {
            "process_id": process_id,
            "query": request.query,
            "type": LogType.SEARCH.value,
            "status": LogStatus.STARTED.value,
            "timestamp": datetime.utcnow(),
            "whitelist": request.whitelist,
            "blacklist": request.blacklist,
        }
    )


async def log_search_complete(
    process_id: str, request: SearchRequest, results: List[Dict]
):
    """Log successful completion of a search request"""
    await db.log_search(
        {
            "process_id": process_id,
            "query": request.query,
            "type": LogType.SEARCH.value,
            "status": LogStatus.COMPLETED.value,
            "timestamp": datetime.utcnow(),
            "results": results,
            "metadata": {
                "urls_found": len(results),
                "urls_scraped": len(results),
            },
        }
    )


async def log_search_error(process_id: str, request: SearchRequest, error: str):
    """Log search error"""
    logger.error(f"Search error: {error}")
    await db.log_search(
        {
            "process_id": process_id,
            "query": request.query,
            "type": LogType.SEARCH.value,
            "status": LogStatus.ERROR.value,
            "timestamp": datetime.utcnow(),
            "error": error,
        }
    )


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, token: str = Depends(verify_token)):
    try:
        process_id = request.process_id or f"search_{int(time.time())}"

        # Log start
        await log_search_start(process_id, request)

        # Get search results
        search_results = await perform_search(
            query=request.query,
            whitelist=request.whitelist,
            blacklist=request.blacklist,
        )

        # Scrape top results
        results = await scraper.scrape_results(search_results[: settings.SCRAPE_LIMIT])

        # Log completion
        await log_search_complete(process_id, request, results)

        return SearchResponse(
            results=results,
            process_id=process_id,
            total_results=len(search_results),
            scraped_results=len(results),
        )

    except Exception as e:
        await log_search_error(process_id, request, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape")
async def scrape_url(url: str, token: str = Depends(verify_token)):
    """Scrape content from a single URL."""
    try:
        result = await scraper.scrape_url(url)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def start_batch_process(
    request: BatchRequest, token: str = Depends(verify_token)
):
    """Start a batch processing job."""
    try:
        process_id = await batch_processor.process_batch(
            queries=request.queries,
            whitelist=request.whitelist,
            blacklist=request.blacklist,
        )
        return {"process_id": process_id}
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{process_id}")
async def get_batch_status(process_id: str, token: str = Depends(verify_token)):
    """Get the status of a batch process."""
    try:
        status = batch_processor.get_process_status(process_id)
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Process not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def serialize_mongodb_doc(doc):
    """Convert MongoDB document to JSON-serializable format."""
    if isinstance(doc, dict):
        return {
            key: (
                str(value)
                if isinstance(value, ObjectId)
                else (
                    value.strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(value, datetime)
                    else (
                        serialize_mongodb_doc(value)
                        if isinstance(value, (dict, list))
                        else value
                    )
                )
            )
            for key, value in doc.items()
        }
    elif isinstance(doc, list):
        return [serialize_mongodb_doc(item) for item in doc]
    return doc


@router.get("/logs")
async def get_logs(
    page: int = 1, per_page: int = 50, token: str = Depends(verify_token)
) -> dict:
    """Get logs with pagination."""
    try:
        # Calculate skip and limit for pagination
        skip = (page - 1) * per_page

        # Get total count
        total = await db.count_logs()

        # Get logs with pagination, sorted by timestamp descending
        logs = await db.get_logs(
            skip=skip, limit=per_page, sort=[("timestamp", -1)]  # Sort by newest first
        )

        # Format the response
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page),
        }
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/scrape/logs")
async def get_scraper_logs(token: str = Depends(verify_token)):
    """Get scraper-specific logs."""
    try:
        logs = await db.get_scraped_content()

        logs_list = []
        for log in logs:
            try:
                meta_data = (
                    json.loads(log.get("meta_data"))
                    if isinstance(log.get("meta_data"), str)
                    else log.get("meta_data", {})
                )
                scraped_data = (
                    json.loads(log.get("scraped_data"))
                    if isinstance(log.get("scraped_data"), str)
                    else log.get("scraped_data", {})
                )

                log_entry = {
                    "id": log.get("id"),
                    "url": log.get("url"),
                    "original_url": log.get("original_url"),
                    "process_id": log.get("process_id"),
                    "timestamp": log.get("timestamp"),
                    "content": log.get("content"),
                    "metadata": meta_data,
                    "scraped_data": scraped_data,
                    "content_size": (
                        len(log.get("content")) if log.get("content") else 0
                    ),
                    "status": "Success" if log.get("content") else "Failed",
                }
                logs_list.append(log_entry)
            except Exception as e:
                logger.error(f"Error processing log {log.get('id')}: {str(e)}")
                continue

        return {"logs": logs_list}
    except Exception as e:
        logger.error(f"Error retrieving scraper logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scraper logs: {str(e)}",
        )


@router.get("/whitelist")
async def get_whitelist(token: str = Depends(verify_token)) -> ListResponse:
    """Get whitelist entries."""
    urls = await db.get_whitelist()
    return ListResponse(urls=urls)


@router.post("/whitelist")
async def update_whitelist(
    request: UpdateListRequest, token: str = Depends(verify_token)
):
    """Add URLs to whitelist."""
    try:
        # Allow empty list but ensure it's a list
        if not isinstance(request.urls, list):
            raise HTTPException(
                status_code=400, detail="URLs must be provided as a list"
            )

        # Clean and validate URLs
        cleaned_urls = [url.strip() for url in request.urls if url and url.strip()]

        # Update whitelist (even if empty)
        await db.update_whitelist(cleaned_urls)
        return {"urls": cleaned_urls}
    except Exception as e:
        logger.error(f"Whitelist update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blacklist")
async def get_blacklist(token: str = Depends(verify_token)) -> ListResponse:
    """Get blacklist entries."""
    urls = await db.get_blacklist()
    return ListResponse(urls=urls)


@router.post("/blacklist")
async def update_blacklist(
    request: UpdateListRequest, token: str = Depends(verify_token)
):
    """Add URLs to blacklist."""
    try:
        # Allow empty list but ensure it's a list
        if not isinstance(request.urls, list):
            raise HTTPException(
                status_code=400, detail="URLs must be provided as a list"
            )

        # Clean and validate URLs
        cleaned_urls = [url.strip() for url in request.urls if url and url.strip()]

        # Update blacklist (even if empty)
        await db.update_blacklist(cleaned_urls)
        return {"urls": cleaned_urls}
    except Exception as e:
        logger.error(f"Blacklist update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/result")
async def store_scrape_result(
    id: str,
    url: str,
    process_id: str,
    content: str = None,
    metadata: Dict = None,
    scraped_data: Dict = None,
    token: str = Depends(verify_token),
):
    """Store scraping result in the database."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Store in database
        await db.store_scraped_content(
            id=id,
            url=url,
            process_id=process_id,
            timestamp=timestamp,
            content=content or "",
            meta_data=json.dumps(metadata or {}),
            scraped_data=json.dumps(scraped_data or {}),
        )

        return {"success": True, "message": "Record stored successfully"}
    except Exception as e:
        logger.error(f"Error storing scrape result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/debug/config")
async def debug_config(token: str = Depends(verify_token)):
    """Debug endpoint to check configuration."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_token": settings.API_TOKEN,  # Be careful with this in production
    }


@router.get("/db/health")
async def db_health(token: str = Depends(verify_token)):
    """Get database health and statistics."""
    try:
        db_instance = await db.ensure_db()
        await db_instance.command("ping")

        stats = await db.get_db_stats()

        return {"status": "healthy", "connection": "active", "stats": stats}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.post("/bulk-search")
async def bulk_search(
    request: BulkSearchRequest, token: str = Depends(verify_token)
) -> dict:
    """Handle bulk search requests."""
    try:
        process_id = str(uuid.uuid4())
        all_results = []
        completed_queries = 0
        failed_queries = 0
        total_queries = len(request.queries)

        # Create initial log entry
        log_entry = SearchLog(
            process_id=process_id,
            query="BULK_SEARCH",
            status=LogStatus.STARTED,
            metadata={
                "total_queries": total_queries,
                "global_lists_enabled": request.globalListsEnabled,
                "progress": {
                    "total": total_queries,
                    "completed": 0,
                    "failed": 0,
                },
            },
        )

        await db.log_search(log_entry.dict())

        for query in request.queries:
            query_id = str(uuid.uuid4())
            try:
                # Combine global and query-specific lists
                whitelist = (
                    query.whitelist + request.globalWhitelist
                    if request.globalListsEnabled
                    else query.whitelist
                )
                blacklist = (
                    query.blacklist + request.globalBlacklist
                    if request.globalListsEnabled
                    else query.blacklist
                )

                # Log individual query start
                await db.log_search(
                    {
                        "process_id": query_id,
                        "parent_process_id": process_id,
                        "query": query.query,
                        "type": LogType.SEARCH.value,
                        "status": LogStatus.PROCESSING.value,
                        "timestamp": datetime.utcnow(),
                        "whitelist": list(set(whitelist)),
                        "blacklist": list(set(blacklist)),
                    }
                )

                # Get search results
                urls = await enhanced_search(
                    query=query.query,
                    num_results=settings.SEARCH_RESULTS_LIMIT,
                    scrape_limit=settings.SCRAPE_LIMIT,
                    whitelist=whitelist,
                    blacklist=blacklist,
                )

                # Process results with scraping
                query_results = []
                scrape_tasks = []

                # Create scraping tasks for URLs
                for url in urls[: settings.SCRAPE_LIMIT]:
                    scrape_tasks.append(scraper.scrape_url(url))

                # Execute scraping tasks concurrently
                if scrape_tasks:
                    scrape_results = await asyncio.gather(
                        *scrape_tasks, return_exceptions=True
                    )

                    # Process scraping results
                    for url, result in zip(
                        urls[: settings.SCRAPE_LIMIT], scrape_results
                    ):
                        if isinstance(result, Exception):
                            query_results.append(
                                {"url": url, "error": str(result), "score": 0}
                            )
                        elif not result.get("error"):
                            query_results.append(
                                {
                                    "url": url,
                                    "content": result.get("content", ""),
                                    "metadata": result.get("metadata", {}),
                                    "score": result.get("score", 0),
                                }
                            )
                        else:
                            query_results.append(
                                {"url": url, "error": result.get("error"), "score": 0}
                            )

                # Add remaining URLs without content
                for url in urls[settings.SCRAPE_LIMIT :]:
                    query_results.append({"url": url})

                # Update individual query log with success
                await db.log_search(
                    {
                        "process_id": query_id,
                        "parent_process_id": process_id,
                        "query": query.query,
                        "type": LogType.SEARCH.value,
                        "status": LogStatus.COMPLETED.value,
                        "timestamp": datetime.utcnow(),
                        "results": query_results,
                        "metadata": {
                            "urls_found": len(urls),
                            "urls_scraped": len(scrape_tasks),
                        },
                    }
                )

                all_results.extend(query_results)
                completed_queries += 1

            except Exception as e:
                failed_queries += 1
                # Log query failure
                await db.log_search(
                    {
                        "process_id": query_id,
                        "parent_process_id": process_id,
                        "query": query.query,
                        "type": LogType.SEARCH.value,
                        "status": LogStatus.FAILED.value,
                        "timestamp": datetime.utcnow(),
                        "error": str(e),
                    }
                )
                logger.error(f"Query error in bulk search: {str(e)}")

            # Update progress in parent log
            await db.log_search(
                {
                    "process_id": process_id,
                    "query": "BULK_SEARCH",
                    "type": LogType.SEARCH.value,
                    "status": LogStatus.PROCESSING.value,
                    "timestamp": datetime.utcnow(),
                    "metadata": {
                        "progress": {
                            "total": total_queries,
                            "completed": completed_queries,
                            "failed": failed_queries,
                        }
                    },
                }
            )

        # Update final bulk search log
        final_status = (
            LogStatus.COMPLETED.value
            if failed_queries < total_queries
            else LogStatus.FAILED.value
        )

        await db.log_search(
            {
                "process_id": process_id,
                "query": "BULK_SEARCH",
                "type": LogType.SEARCH.value,
                "status": final_status,
                "timestamp": datetime.utcnow(),
                "results": all_results,
                "metadata": {
                    "total_queries": total_queries,
                    "completed_queries": completed_queries,
                    "failed_queries": failed_queries,
                    "global_lists_enabled": request.globalListsEnabled,
                    "progress": {
                        "total": total_queries,
                        "completed": completed_queries,
                        "failed": failed_queries,
                    },
                },
            }
        )

        return {
            "process_id": process_id,
            "status": final_status,
            "results": all_results,
            "metadata": {
                "total_queries": total_queries,
                "completed_queries": completed_queries,
                "failed_queries": failed_queries,
            },
        }

    except Exception as e:
        logger.error(f"Bulk search error: {str(e)}")
        await db.log_search(
            {
                "process_id": process_id,
                "query": "BULK_SEARCH",
                "type": LogType.SEARCH.value,
                "status": LogStatus.ERROR.value,
                "timestamp": datetime.utcnow(),
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/settings")
async def get_settings(token: str = Depends(verify_token)):
    """Get current settings."""
    try:
        return {"maxResultsPerQuery": settings.MAX_RESULTS_PER_QUERY}
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/settings")
async def update_settings(request: SettingsUpdate, token: str = Depends(verify_token)):
    """Update settings."""
    try:
        # Validate max results
        if request.maxResultsPerQuery < 1 or request.maxResultsPerQuery > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max results must be between 1 and 100",
            )

        # Update settings in database or config
        settings.MAX_RESULTS_PER_QUERY = request.maxResultsPerQuery

        return {"maxResultsPerQuery": settings.MAX_RESULTS_PER_QUERY}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Add all other route handlers here...

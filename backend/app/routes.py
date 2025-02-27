from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Header,
    status,
    Response,
    UploadFile,
    File,
)
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from .scraper import WebScraper, enhanced_search
from .config import settings
from .db.mongodb import db as mongodb
from .batch_processor import batch_processor
from .api import (
    SearchRequest,
    SearchResponse,
    ListResponse,
    UpdateListRequest,
    BatchRequest,
)
from app.models import LogType, LogStatus, BaseLog, SearchLog, ScrapeLog
from .models.settings import SearchSettings
import asyncio
from bson import ObjectId
from pydantic import BaseModel
import uuid
from .services.search import perform_search
import csv
from io import StringIO
from app.scraper import scraper

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


class BulkScrapeRequest(BaseModel):
    urls: List[str]


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
    await mongodb.log_search(
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
    await mongodb.log_search(
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
    await mongodb.log_search(
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
        await log_search_start(process_id, request)

        try:
            # Get current settings including DB overrides
            search_settings = await settings.get_search_settings()

            search_results = await perform_search(
                query=request.query,
                whitelist=request.whitelist,
                blacklist=request.blacklist,
                limit=search_settings["SEARCH_RESULTS_LIMIT"],
                min_score=search_settings["MIN_SCORE_THRESHOLD"],
            )

            # Scrape results
            # results = await scraper.scrape_results(
            #     search_results[: search_settings["SCRAPE_LIMIT"]]
            # )

            results = await scraper.scrape_results(search_results)

            await log_search_complete(process_id, request, results)

            return SearchResponse(
                results=results,
                process_id=process_id,
                total_results=len(search_results),
                scraped_results=len(results),
            )

        except Exception as e:
            await log_search_error(process_id, request, str(e))
            raise

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape")
async def scrape_url(url: str, token: str = Depends(verify_token)):
    """Scrape content from a single URL."""
    try:
        result = await scraper.scrape_url(url)

        # Log the scrape attempt
        await mongodb.log_scrape(
            {
                "process_id": str(uuid.uuid4()),
                "url": url,
                "timestamp": datetime.utcnow(),
                "type": LogType.SCRAPE.value,
                "status": (
                    LogStatus.COMPLETED.value
                    if not result.get("error")
                    else LogStatus.ERROR.value
                ),
                "result": result,
                "error": result.get("error"),
            }
        )

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
    """Get search logs with pagination"""
    try:
        skip = (page - 1) * per_page
        logs = await mongodb.get_logs(
            skip=skip, limit=per_page, sort=[("timestamp", -1)]
        )
        total = await mongodb.count_logs()

        return {"logs": logs, "total": total, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/scrape/logs")
async def get_scrape_logs(
    page: int = 1, per_page: int = 50, token: str = Depends(verify_token)
):
    """Get scraper-specific logs with pagination"""
    try:
        logger.info(f"Fetching scrape logs - page: {page}, per_page: {per_page}")
        skip = (page - 1) * per_page

        logs = await mongodb.get_scrape_logs(
            skip=skip, limit=per_page, sort=[("timestamp", -1)]
        )
        logger.info("Successfully fetched logs")

        total = await mongodb.count_scrape_logs()
        logger.info(f"Total scrape logs: {total}")

        return {"logs": logs, "total": total, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"Error in get_scrape_logs endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch scrape logs: {str(e)}"
        )


@router.get("/whitelist")
async def get_whitelist(token: str = Depends(verify_token)) -> ListResponse:
    """Get whitelist entries."""
    try:
        result = await mongodb.get_whitelist()
        return ListResponse(urls=result["urls"])
    except Exception as e:
        logger.error(f"Error fetching whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/whitelist")
async def update_whitelist(
    request: UpdateListRequest, token: str = Depends(verify_token)
) -> ListResponse:
    """Update whitelist URLs."""
    try:
        # Clean and validate URLs
        cleaned_urls = [url.strip() for url in request.urls if url and url.strip()]
        result = await mongodb.update_whitelist(cleaned_urls)
        return ListResponse(urls=result["urls"])
    except Exception as e:
        logger.error(f"Error updating whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/blacklist")
async def get_blacklist(token: str = Depends(verify_token)) -> ListResponse:
    """Get blacklist entries."""
    try:
        result = await mongodb.get_blacklist()
        return ListResponse(urls=result["urls"])
    except Exception as e:
        logger.error(f"Error fetching blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/blacklist")
async def update_blacklist(
    request: UpdateListRequest, token: str = Depends(verify_token)
) -> ListResponse:
    """Update blacklist URLs."""
    try:
        # Clean and validate URLs
        cleaned_urls = [url.strip() for url in request.urls if url and url.strip()]
        result = await mongodb.update_blacklist(cleaned_urls)
        return ListResponse(urls=result["urls"])
    except Exception as e:
        logger.error(f"Error updating blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


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
        await mongodb.store_scraped_content(
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
        db_instance = await mongodb.ensure_db()
        await db_instance.command("ping")

        stats = await mongodb.get_db_stats()

        return {"status": "healthy", "connection": "active", "stats": stats}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.post("/bulk-search")
async def bulk_search(request: BulkSearchRequest, token: str = Depends(verify_token)):
    """Start bulk search process"""
    process_id = f"bulk_{int(time.time())}"

    try:
        # Create initial bulk search log
        await mongodb.log_search(
            {
                "process_id": process_id,
                "query": "BULK_SEARCH",
                "type": LogType.SEARCH.value,
                "status": LogStatus.STARTED.value,
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "progress": {
                        "total": len(request.queries),
                        "completed": 0,
                        "failed": 0,
                    }
                },
            }
        )

        # Start background task for processing
        asyncio.create_task(process_bulk_search(process_id, request))

        return {"process_id": process_id}

    except Exception as e:
        logger.error(f"Bulk search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_bulk_search(process_id: str, request: BulkSearchRequest):
    """Process bulk search in background"""
    total_queries = len(request.queries)
    completed_queries = 0
    failed_queries = 0
    child_logs = []

    try:
        # Get current settings
        search_settings = await settings.get_search_settings()

        for query in request.queries:
            query_id = f"{process_id}_q{len(child_logs) + 1}"

            try:
                # Use the same search logic as single search
                whitelist = (
                    request.globalWhitelist
                    if request.globalListsEnabled
                    else query.whitelist
                )
                blacklist = (
                    request.globalBlacklist
                    if request.globalListsEnabled
                    else query.blacklist
                )

                search_results = await perform_search(
                    query=query.query,
                    whitelist=whitelist,
                    blacklist=blacklist,
                    limit=search_settings["SEARCH_RESULTS_LIMIT"],
                    min_score=search_settings["MIN_SCORE_THRESHOLD"],
                )

                # Scrape results
                # scraped_results = await scraper.scrape_results(
                #     search_results[: search_settings["SCRAPE_LIMIT"]]
                # )

                scraped_results = await scraper.scrape_results(search_results)

                # Create child log
                child_log = {
                    "process_id": query_id,
                    "parent_process_id": process_id,
                    "query": query.query,
                    "type": LogType.SEARCH.value,
                    "status": LogStatus.COMPLETED.value,
                    "timestamp": datetime.utcnow(),
                    "results": scraped_results,
                    "metadata": {
                        "total_results": len(search_results),
                        "scraped_results": len(scraped_results),
                        "whitelist_matches": sum(
                            1 for r in search_results if r.get("whitelist_match", False)
                        ),
                    },
                }

                child_logs.append(child_log)
                completed_queries += 1

            except Exception as e:
                failed_queries += 1
                child_log = {
                    "process_id": query_id,
                    "parent_process_id": process_id,
                    "query": query.query,
                    "type": LogType.SEARCH.value,
                    "status": LogStatus.FAILED.value,
                    "timestamp": datetime.utcnow(),
                    "error": str(e),
                }
                child_logs.append(child_log)
                logger.error(f"Query error in bulk search: {str(e)}")

            # Update progress
            await mongodb.log_search(
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
                    "child_logs": child_logs,
                    "_replace": True,
                }
            )

        # Final update
        final_status = (
            LogStatus.COMPLETED.value
            if failed_queries < total_queries
            else LogStatus.FAILED.value
        )
        await mongodb.log_search(
            {
                "process_id": process_id,
                "query": "BULK_SEARCH",
                "type": LogType.SEARCH.value,
                "status": final_status,
                "timestamp": datetime.utcnow(),
                "child_logs": child_logs,
                "metadata": {
                    "progress": {
                        "total": total_queries,
                        "completed": completed_queries,
                        "failed": failed_queries,
                    }
                },
                "_replace": True,
            }
        )

    except Exception as e:
        logger.error(f"Bulk search processing error: {str(e)}")
        await mongodb.log_search(
            {
                "process_id": process_id,
                "query": "BULK_SEARCH",
                "type": LogType.SEARCH.value,
                "status": LogStatus.ERROR.value,
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "child_logs": child_logs,
                "_replace": True,
            }
        )


@router.get("/settings")
async def get_settings():
    """Get current settings"""
    settings = await SearchSettings.get_settings()
    return {
        "maxResultsPerQuery": settings.maxResultsPerQuery,
        "searchResultsLimit": settings.searchResultsLimit,
        "scrapeLimit": settings.scrapeLimit,
        "minScoreThreshold": settings.minScoreThreshold,
        "jinaRateLimit": settings.jinaRateLimit,
        "searchRateLimit": settings.searchRateLimit,
    }


@router.post("/settings")
async def update_settings(settings: SearchSettings):
    """Update settings"""
    await SearchSettings.update_settings(settings.dict())
    return {"status": "success"}


@router.get("/bulk-search/template", response_class=Response)
async def get_bulk_search_template():
    """Get CSV template for bulk search"""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["query", "whitelist", "blacklist"])
    writer.writerow(
        ["example query", "domain1.com,domain2.com", "exclude1.com,exclude2.com"]
    )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=bulk_search_template.csv"
        },
    )


@router.post("/bulk-scrape")
async def bulk_scrape(request: BulkScrapeRequest, token: str = Depends(verify_token)):
    """Start bulk scraping process"""
    process_id = f"bulk_scrape_{int(time.time())}"

    try:
        # Start background task for processing
        asyncio.create_task(process_bulk_scrape(process_id, request.urls))
        return {"process_id": process_id}
    except Exception as e:
        logger.error(f"Bulk scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-scrape/upload")
async def upload_bulk_scrape(
    file: UploadFile = File(...), token: str = Depends(verify_token)
):
    """Handle CSV upload for bulk scraping"""
    try:
        content = await file.read()
        text = content.decode()
        urls = []

        csv_reader = csv.reader(StringIO(text))
        next(csv_reader)  # Skip header row

        for row in csv_reader:
            if row and row[0]:  # Check if row has URL
                urls.append(row[0].strip())

        return await bulk_scrape(BulkScrapeRequest(urls=urls), token)

    except Exception as e:
        logger.error(f"CSV upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bulk-search/{process_id}")
async def get_bulk_search_details(
    process_id: str, token: str = Depends(verify_token)
) -> Dict[str, Any]:
    try:
        # Get the main log
        log = await mongodb.get_search_log(process_id)
        if not log:
            raise HTTPException(
                status_code=404, detail=f"Log not found for process ID: {process_id}"
            )

        # If it's a bulk search, get child logs
        if log.get("query") == "BULK_SEARCH":
            child_logs = await mongodb.get_child_logs(process_id)
            response = {**log, "children": child_logs}
        else:
            # For regular searches, just return the log
            response = log

        return response
    except Exception as e:
        logger.error(f"Error retrieving log details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving log details: {str(e)}"
        )


# Add all other route handlers here...

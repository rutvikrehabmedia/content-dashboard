from fastapi import APIRouter, HTTPException
import uuid
import logging
from ..scraper import enhanced_search
from ..services.search import process_search_results, calculate_relevance_score
from ..api import SearchRequest
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search")
async def search(request: SearchRequest):
    logger.info(f"\n{'='*50}")
    logger.info(f"New search request: {request.query}")

    try:
        # Get initial search results with scores
        scored_urls = await enhanced_search(
            query=request.query,
            num_results=settings.SEARCH_RESULTS_LIMIT,
            scrape_limit=settings.SCRAPE_LIMIT,
            whitelist=request.whitelist,
            blacklist=request.blacklist,
        )

        logger.info(f"Found {len(scored_urls)} URLs after initial search and filtering")

        # Convert scored URLs to results format
        results = []
        for scored_url in scored_urls:
            results.append(
                {
                    "url": scored_url["url"],
                    "score": scored_url["score"],  # Preserve the score
                    "metadata": {},
                    "content": "",
                    "title": scored_url["url"],
                    "snippet": "",
                }
            )

        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Log final results with detailed scoring
        logger.info("\nFinal scored results:")
        for result in results:
            logger.info(f"\nURL: {result['url']}")
            logger.info(f"Score: {result.get('score', 0):.2f}")
            logger.info(f"Title: {result.get('title', 'No title')}")
            logger.info("-" * 30)

        return {
            "results": results,
            "process_id": str(uuid.uuid4()),
            "total_results": len(scored_urls),
            "scraped_results": len(results),
        }

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/logs")
async def get_recent_logs():
    """Get recent log entries"""
    try:
        log_file = Path(__file__).parent.parent.parent / "logs" / "app.log"
        if not log_file.exists():
            return {"message": "No logs found"}

        # Get last 100 lines
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]

        return {"logs": lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

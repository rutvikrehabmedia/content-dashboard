# Copy the entire content from google-sheet-dashboard/app/scrapper.py
# This file contains WebScraper class and enhanced_search function

from typing import List, Dict, Set, Optional
import asyncio
from .db import db
import time
from urllib.parse import urlparse, quote_plus, urljoin
import aiohttp
import urllib.parse
import os
from googlesearch import search as gsearch
from duckduckgo_search import DDGS
import random
import json
from difflib import SequenceMatcher
import logging
import validators
import re
from functools import lru_cache
from bson.objectid import ObjectId
from datetime import datetime
from .config import settings
from .jina_extractor import JinaExtractor
from .services.search import calculate_relevance_score, process_search_results

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Copy all the functions and classes from the original scrapper.py
@lru_cache(maxsize=1000)
def sanitize_query(query: str) -> str:
    """Sanitize the search query with caching for performance."""
    try:
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-]", " ", query)
        sanitized = re.sub(r"\s+", " ", sanitized)
        return sanitized.strip()[:150] or "invalid query"
    except Exception as e:
        logger.error(f"Error sanitizing query: {str(e)}")
        return query


def extract_search_result(item: Dict, source: str) -> Dict:
    """Safely extract search result fields with proper error handling."""
    try:
        url = item.get("link") or item.get("url")
        title = item.get("title") or url
        snippet = (
            item.get("body") or item.get("description") or item.get("snippet") or ""
        )

        if not url:
            logger.warning(f"No URL found in search result from {source}")
            return None

        if not is_valid_url(url):
            logger.warning(f"Invalid URL found in search result from {source}: {url}")
            return None

        return {"url": url, "title": title, "snippet": snippet, "source": source}
    except Exception as e:
        logger.error(f"Error extracting search result from {source}: {str(e)}")
        return None


async def is_valid_url(url: str, timeout: int = 5) -> bool:
    """Validate URL format and accessibility asynchronously."""
    try:
        if not url or not isinstance(url, str):
            return False

        if not validators.url(url):
            return False

        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in [
            "http",
            "https",
        ]:
            return False

        if len(url) > 2000:  # Most browsers' URL length limit
            return False

        # Optional: Check if URL is accessible
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(
                    url, timeout=timeout, allow_redirects=True
                ) as response:
                    return response.status < 400
            except:
                return (
                    True  # Consider URL valid if we can't check (avoid false negatives)
                )

    except Exception as e:
        logger.error(f"URL validation error for {url}: {str(e)}")
        return False


def is_domain_match(url: str, pattern: str) -> bool:
    """Check if a URL matches a domain pattern, including subdomains."""
    try:
        url_domain = urlparse(url).netloc.lower()
        pattern = pattern.lower()

        # Remove www. from both
        url_domain = url_domain.replace("www.", "")
        pattern = pattern.replace("www.", "")

        # Check exact match
        if url_domain == pattern:
            return True

        # Check if URL is a subdomain of pattern
        if url_domain.endswith("." + pattern):
            return True

        return False
    except:
        return False


def filter_and_prioritize_urls(
    urls: List[str],
    query_whitelist: List[str],
    query_blacklist: List[str],
    global_whitelist: List[str],
    global_blacklist: List[str],
) -> List[str]:
    """Filter and prioritize URLs based on whitelist and blacklist rules."""
    # Combine blacklists (query blacklist takes precedence)
    all_blacklist = list(set(query_blacklist + global_blacklist))

    # Filter out blacklisted domains
    filtered_urls = []
    for url in urls:
        is_blacklisted = any(is_domain_match(url, pattern) for pattern in all_blacklist)
        if not is_blacklisted:
            filtered_urls.append(url)

    # Combine whitelists
    query_whitelisted = []
    global_whitelisted = []
    other_urls = []

    for url in filtered_urls:
        if any(is_domain_match(url, pattern) for pattern in query_whitelist):
            query_whitelisted.append(url)
        elif any(is_domain_match(url, pattern) for pattern in global_whitelist):
            global_whitelisted.append(url)
        else:
            other_urls.append(url)

    return query_whitelisted + global_whitelisted + other_urls


class SearchProvider:
    """Base class for search providers with rate limiting."""

    def __init__(self):
        self.last_request = 0
        self.min_delay = 2  # Minimum delay between requests

    async def wait_for_rate_limit(self):
        """Implement rate limiting."""
        now = time.time()
        if now - self.last_request < self.min_delay:
            await asyncio.sleep(self.min_delay - (now - self.last_request))
        self.last_request = time.time()

    async def search(self, query: str, num_results: int = 20) -> List[Dict]:
        raise NotImplementedError


class GoogleSearchProvider(SearchProvider):
    """Primary search provider using Google."""

    async def search(self, query: str, num_results: int = 20) -> List[Dict]:
        try:
            logger.info(f"Starting Google search for query: {query}")
            results = []

            # Use the passed num_results
            search_results = list(
                gsearch(query, num=num_results, stop=num_results, pause=2)
            )

            for url in search_results:
                if validators.url(url):
                    result = {
                        "url": url,
                        "title": url,
                        "snippet": "",
                        "source": "google",
                    }
                    if result not in results:
                        results.append(result)
                        logger.info(f"Found valid URL: {url}")

            logger.info(f"Google search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in Google search: {str(e)}")
            return []


class DuckDuckGoProvider(SearchProvider):
    """Fallback search provider using DuckDuckGo."""

    def __init__(self):
        super().__init__()
        self.max_retries = 3
        self.retry_delay = 5

    async def search(self, query: str, num_results: int = 20) -> List[Dict]:
        try:
            logger.info(f"Starting DuckDuckGo search for query: {query}")
            results = []

            # Less aggressive sanitization for DDG
            sanitized_query = query.replace(",", " ").strip()
            logger.info(f"Modified query for DDG: {sanitized_query}")

            # Try different regions if one fails
            regions = ["us-en", "wt-wt", "uk-en"]

            for region in regions:
                for attempt in range(self.max_retries):
                    try:
                        with DDGS() as ddgs:
                            # Get text results from DuckDuckGo
                            ddg_results = list(
                                ddgs.text(
                                    sanitized_query,
                                    region=region,
                                )
                            )

                            for item in ddg_results:
                                url = item.get("link")
                                if url and validators.url(url):
                                    result = {
                                        "url": url,
                                        "title": item.get("title", url),
                                        "snippet": item.get("body", ""),
                                        "source": "duckduckgo",
                                    }
                                    if result not in results:
                                        results.append(result)
                                        logger.info(
                                            f"Found valid URL from DuckDuckGo: {url}"
                                        )

                            if results:  # If we got results, break both loops
                                break

                    except Exception as e:
                        if "Ratelimit" in str(e):
                            wait_time = self.retry_delay * (attempt + 1)
                            logger.warning(
                                f"Rate limited for region {region}, waiting {wait_time} seconds"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Error with region {region}: {str(e)}")
                            break  # Try next region

                if results:  # If we got results, break regions loop
                    break
                await asyncio.sleep(2)  # Wait before trying next region

            logger.info(
                f"DuckDuckGo search completed. Found {len(results)} valid results"
            )
            return results
        except Exception as e:
            logger.error(f"Error in DuckDuckGo search: {str(e)}")
            return []


class WebScraper:
    """Improved web scraper with caching and parallel processing."""

    def __init__(self):
        self.cache = {}  # URL -> result mapping
        self.cache_ttl = 3600  # 1 hour
        self.jina = JinaExtractor()

    async def scrape_url(self, url_data: Dict) -> Dict:
        """Scrape content from a URL with caching."""
        try:
            url = url_data["url"] if isinstance(url_data, dict) else url_data

            # Check cache
            if url in self.cache:
                cache_entry = self.cache[url]
                if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                    logger.info(f"Cache hit for URL: {url}")
                    return cache_entry["data"]

            logger.info(f"Processing URL: {url}")

            # Extract content using Jina
            jina_result = await self.jina.extract_content(url)

            if jina_result["status"] == "error":
                return {"error": jina_result["error"]}

            # Create unique ID for storage
            doc_id = str(ObjectId())
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            # Preserve the score if it was passed
            score = url_data.get("score", 0) if isinstance(url_data, dict) else 0

            result = {
                "id": doc_id,
                "url": url,
                "score": score,
                "content": jina_result["content"],
                "timestamp": timestamp,
                "metadata": jina_result["metadata"],
                "title": (
                    url_data.get("title", url) if isinstance(url_data, dict) else url
                ),
                "snippet": (
                    url_data.get("snippet", "") if isinstance(url_data, dict) else ""
                ),
            }

            # Store in database
            try:
                await db.store_scraped_content(
                    id=doc_id,
                    url=url,
                    content=jina_result["content"],
                    timestamp=timestamp,
                    meta_data=json.dumps(jina_result["metadata"]),
                    scraped_data=json.dumps(result),
                )
                logger.info(f"Stored scrape result for URL: {url}")
            except Exception as e:
                logger.error(f"Failed to store scrape result for {url}: {str(e)}")

            # Update cache
            self.cache[url] = {"timestamp": time.time(), "data": result}
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error scraping {url}: {error_msg}")
            return {"error": error_msg}

    async def close(self):
        """Cleanup resources."""
        await self.jina.close()


async def enhanced_search(
    query: str,
    num_results: int = 20,
    scrape_limit: int = 2,
    whitelist: List[str] = None,
    blacklist: List[str] = None,
) -> List[Dict]:
    try:
        logger.info(f"Starting enhanced search for query: {query}")

        # Get search results using num_results
        google_provider = GoogleSearchProvider()
        search_results = await google_provider.search(query, num_results)

        if not search_results:
            logger.error("No results found from search provider")
            return []

        # Score and filter results
        scored_results = []
        seen_urls = set()

        for result in search_results:
            url = result["url"]
            if url in seen_urls:
                continue

            # Calculate relevance score
            score = calculate_relevance_score(
                query,
                {
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "domain": urlparse(url).netloc,
                },
            )

            if score > 0:
                scored_results.append(
                    {
                        "url": url,
                        "score": score,
                        "title": result.get("title", url),
                        "snippet": result.get("snippet", ""),
                    }
                )
                seen_urls.add(url)

        # Sort by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Apply whitelist/blacklist filtering
        filtered_urls = filter_and_prioritize_urls(
            [r["url"] for r in scored_results],
            whitelist or [],
            blacklist or [],
            await db.get_whitelist(),
            await db.get_blacklist(),
        )

        # Keep only filtered URLs while preserving scores
        final_results = [
            result for result in scored_results if result["url"] in filtered_urls
        ][:scrape_limit]

        # Scrape the content for final results
        for result in final_results:
            try:
                scraped_data = await scraper.scrape_url(result)
                if "error" not in scraped_data:
                    result.update(scraped_data)
            except Exception as e:
                logger.error(f"Error scraping result: {str(e)}")

        logger.info(f"Found {len(final_results)} relevant URLs after filtering")
        return final_results

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return []


# Initialize scraper
scraper = WebScraper()

# Copy the rest of the functions and classes...

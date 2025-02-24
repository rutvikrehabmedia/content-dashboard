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
from .models import SearchResult
from .services.search import (
    calculate_relevance_score,
    process_search_results,
    google_search,
    ddg_search,
)

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
        self.session = None

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

    async def scrape_results(self, search_results: List[SearchResult]) -> List[Dict]:
        """Scrape multiple search results"""
        try:
            results = []
            scrape_tasks = []

            # Create scraping tasks for all URLs
            for result in search_results:
                scrape_tasks.append(self.scrape_url(result.url))

            # Execute scraping tasks concurrently
            if scrape_tasks:
                scrape_results = await asyncio.gather(
                    *scrape_tasks, return_exceptions=True
                )

                # Process scraping results
                for result, scrape_result in zip(search_results, scrape_results):
                    if isinstance(scrape_result, Exception):
                        results.append(
                            {
                                "url": result.url,
                                "error": str(scrape_result),
                                "score": result.score,
                            }
                        )
                    elif not scrape_result.get("error"):
                        results.append(
                            {
                                "url": result.url,
                                "content": scrape_result.get("content", ""),
                                "metadata": scrape_result.get("metadata", {}),
                                "score": result.score,
                            }
                        )
                    else:
                        results.append(
                            {
                                "url": result.url,
                                "error": scrape_result.get("error"),
                                "score": result.score,
                            }
                        )

            return results

        except Exception as e:
            logger.error(f"Error scraping results: {str(e)}")
            return [
                {"url": r.url, "error": str(e), "score": r.score}
                for r in search_results
            ]


async def enhanced_search(
    query: str,
    num_results: int = 10,
    scrape_limit: int = 5,
    whitelist: List[str] = None,
    blacklist: List[str] = None,
) -> List[str]:
    try:
        # Split query into keywords
        keywords = query.lower().split()

        # Get initial search results
        search_results = await search_web(
            query, num_results * 2
        )  # Get more results initially

        # Score and filter results
        scored_results = []
        for url in search_results:
            try:
                domain = urlparse(url).netloc.lower()
                full_url = url.lower()

                # Initialize score
                score = 0

                # Domain and URL scoring
                for keyword in keywords:
                    if keyword in domain:
                        score += 2  # Higher weight for domain matches
                    if keyword in full_url:
                        score += 1  # Lower weight for URL path matches

                # Filter based on whitelist/blacklist
                if whitelist and not any(domain.endswith(w.lower()) for w in whitelist):
                    continue
                if blacklist and any(domain.endswith(b.lower()) for b in blacklist):
                    continue

                scored_results.append((url, score))

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                continue

        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # If no results pass filters, take top results ignoring filters
        if not scored_results and search_results:
            logger.info("No results passed filters, returning unfiltered results")
            scored_results = [(url, 0) for url in search_results[:num_results]]

        # Extract URLs from scored results
        filtered_urls = [url for url, _ in scored_results[:num_results]]

        # If still no results, perform a broader search
        if not filtered_urls:
            logger.info("Performing broader search")
            # Remove quotes and special operators for broader matching
            broad_query = " ".join(keywords)
            search_results = await search_web(broad_query, num_results)
            filtered_urls = search_results[:num_results]

        logger.info(
            f"Enhanced search completed. Returning {len(filtered_urls)} results"
        )
        return filtered_urls

    except Exception as e:
        logger.error(f"Enhanced search error: {str(e)}")
        raise


async def search_web(query: str, num_results: int = 10) -> List[str]:
    """
    Perform web search using multiple providers and combine results.
    """
    try:
        logger.info(f"Starting web search for query: {query}")

        # Initialize search providers
        google_provider = GoogleSearchProvider()
        ddg_provider = DuckDuckGoProvider()

        # Perform searches concurrently
        google_results, ddg_results = await asyncio.gather(
            google_provider.search(query, num_results),
            ddg_provider.search(query, num_results),
        )

        # Combine and deduplicate results
        all_urls = set()
        combined_results = []

        for result in google_results + ddg_results:
            url = result.get("url")
            if url and url not in all_urls and await is_valid_url(url):
                all_urls.add(url)
                combined_results.append(url)

        # Limit to requested number of results
        final_results = combined_results[:num_results]

        logger.info(
            f"Web search completed. Found {len(final_results)} unique valid URLs"
        )
        return final_results

    except Exception as e:
        logger.error(f"Web search error: {str(e)}")
        raise


# Initialize scraper
scraper = WebScraper()

# Copy the rest of the functions and classes...

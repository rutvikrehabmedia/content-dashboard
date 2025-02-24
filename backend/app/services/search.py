from typing import List, Dict, Set
from urllib.parse import urlparse
import logging
import os
from ..config import settings
from ..models import SearchResult
from googlesearch import search as gsearch
from duckduckgo_search import DDGS
import asyncio
from ..utils.domain import check_domain_lists, is_domain_match

logger = logging.getLogger(__name__)


def calculate_relevance_score(query: str, result: Dict) -> float:
    """Calculate relevance score using a simplified but effective approach."""
    try:
        url = result.get("url", "").lower()
        logger.info(f"\n{'='*50}")
        logger.info(f"Calculating score for URL: {url}")

        # Extract organization name and location
        parts = query.split("-")
        org_name = parts[0].strip().lower()
        location = parts[1].strip().lower() if len(parts) > 1 else ""

        logger.info("Query analysis:")
        logger.info(f"- Organization: {org_name}")
        logger.info(f"- Location: {location}")

        score = 0.0
        score_breakdown = []

        # 1. Domain match with whitelist bonus
        domain = urlparse(url).netloc.lower().replace("www.", "")
        org_words = org_name.split()

        logger.info(f"\nDomain analysis:")
        logger.info(f"- Checking domain: {domain}")
        logger.info(f"- Organization words: {org_words}")

        # Check for organization name in domain
        matching_words = [
            word for word in org_words if len(word) > 4 and word in domain
        ]
        if matching_words:
            score += 0.6
            score_breakdown.append(f"Domain match (+0.6): Found words {matching_words}")
            # Org domain bonus
            if domain.endswith(".org"):
                score += 0.2
                score_breakdown.append("Org domain bonus (+0.2)")

        # 2. Location match in URL or title
        if location:
            location_words = [word.strip() for word in location.split(",")]
            url_text = f"{url} {result.get('title', '')}".lower()
            matching_locations = [
                loc for loc in location_words if loc.lower() in url_text
            ]
            if matching_locations:
                score += 0.4
                score_breakdown.append(
                    f"Location match (+0.4): Found locations {matching_locations}"
                )

        # Apply penalties
        penalty_patterns = [
            "linkedin.com",
            "indeed.com",
            "ziprecruiter.com",
            "jobs",
            "careers",
        ]
        for pattern in penalty_patterns:
            if pattern in url:
                score -= 0.3
                score_breakdown.append(f"Penalty (-0.3): Found {pattern}")

        # Add whitelist bonus if applicable
        if "whitelist_match" in result and result["whitelist_match"]:
            score += 0.5
            score_breakdown.append("Whitelist bonus (+0.5)")

        final_score = max(0.0, min(1.0, score))

        # Log detailed breakdown
        logger.info("\nScore breakdown:")
        for detail in score_breakdown:
            logger.info(f"- {detail}")
        logger.info(f"Final score: {final_score:.2f}")
        logger.info("=" * 50)

        return final_score

    except Exception as e:
        logger.error(f"Error calculating score: {str(e)}")
        return 0.0


async def process_search_results(
    query: str,
    results: List[Dict],
    whitelist: List[str] = None,
    blacklist: List[str] = None,
    min_score: float = None,
) -> List[Dict]:
    """Process search results with proper domain matching and whitelist prioritization"""
    all_scored_results = []
    seen_domains = set()
    threshold = min_score or settings.MIN_SCORE_THRESHOLD

    # First pass: Process all results and mark whitelist matches
    for result in results:
        try:
            print(result)
            url = result.get("url", "")
            if not url:
                continue

            print("STAGE 1")
            domain = urlparse(url).netloc.lower()
            if domain in seen_domains:
                continue

            print("STAGE 2")
            # Use check_domain_lists for consistent domain checking
            domain_check = check_domain_lists(url, whitelist, blacklist)
            if not domain_check and blacklist:  # If blacklisted, skip
                continue

            print("STAGE 3")
            # Mark whitelist match
            result["whitelist_match"] = bool(
                whitelist
                and any(is_domain_match(url, pattern) for pattern in whitelist)
            )

            # Calculate score
            score = calculate_relevance_score(query, result)
            result["score"] = score

            if score >= threshold:
                seen_domains.add(domain)
                all_scored_results.append(result)

            print(result)
            print(all_scored_results)

        except Exception as e:
            logger.error(f"Error processing result: {str(e)}")
            continue

    # Sort results by score and whitelist match
    all_scored_results.sort(
        key=lambda x: (x.get("whitelist_match", False), x.get("score", 0)), reverse=True
    )

    # If we have whitelist but no matching results, return top scoring non-whitelisted results
    if whitelist and not any(
        r.get("whitelist_match", False) for r in all_scored_results
    ):
        logger.info("No whitelist matches found, returning top scoring results")
        return all_scored_results[: settings.SEARCH_RESULTS_LIMIT]

    return all_scored_results[: settings.SEARCH_RESULTS_LIMIT]


async def perform_search(
    query: str,
    whitelist: List[str] = None,
    blacklist: List[str] = None,
    limit: int = None,
    min_score: float = None,
) -> List[Dict]:
    """Main search function that orchestrates the entire search process."""
    try:
        # Use provided limits or fall back to settings
        search_limit = limit or settings.SEARCH_RESULTS_LIMIT
        score_threshold = min_score or settings.MIN_SCORE_THRESHOLD

        # Get raw search results
        raw_results = await get_search_results(query, num_results=search_limit)

        # Process and score results
        processed_results = await process_search_results(
            query=query,
            results=raw_results,
            whitelist=whitelist,
            blacklist=blacklist,
            min_score=score_threshold,
        )

        return processed_results[:search_limit]

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise


async def get_search_results(query: str, num_results: int) -> List[Dict]:
    """Get search results from Google or DuckDuckGo"""
    try:
        # Try Google first
        results = await google_search(query, num_results)

        if results:
            logger.info("Using Google search results")
            return results

        # Fallback to DuckDuckGo if needed
        logger.info("No Google results, falling back to DuckDuckGo")
        return await perform_ddg_search(query, num_results)

    except Exception as e:
        logger.error(f"Search provider error: {str(e)}")
        return []


async def google_search(query: str, num_results: int) -> List[Dict]:
    """Perform Google search using googlesearch-python package"""
    try:
        results = []
        # googlesearch-python uses 'num' parameter, not 'num_results'
        for result in gsearch(query, num=num_results, lang="en", stop=num_results):
            if result:  # Ensure we have a valid URL
                results.append(
                    {
                        "url": result,
                        "title": result,  # We'll get actual title during scraping
                        "snippet": "",
                        "score": 0,  # Initial score
                    }
                )

        logger.info(f"Google search found {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Google search error: {str(e)}")
        return []


async def perform_ddg_search(query: str, num_results: int = 10) -> List[str]:
    """Perform DuckDuckGo search with retries and fallback"""
    try:
        # First try with HTML endpoint
        results = await search_ddg_html(query, num_results)
        if results:
            return results

        # Fallback to lite endpoint
        results = await search_ddg_lite(query, num_results)
        if results:
            return results

        # If both fail, try API endpoint
        return await search_ddg_api(query, num_results)

    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return []


async def search_ddg_html(query: str, num_results: int) -> List[str]:
    """Search using DuckDuckGo HTML endpoint"""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=num_results):
                if isinstance(r, dict) and "link" in r:
                    results.append(
                        {
                            "url": r["link"],
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                        }
                    )
            return results
    except Exception as e:
        logger.error(f"DDG HTML search error: {e}")
        return []


async def search_ddg_lite(query: str, num_results: int) -> List[str]:
    """Search using DuckDuckGo Lite endpoint"""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=num_results, backend="lite"):
                if isinstance(r, dict) and "link" in r:
                    results.append(
                        {
                            "url": r["link"],
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                        }
                    )
            return results
    except Exception as e:
        logger.error(f"DDG Lite search error: {e}")
        return []


async def search_ddg_api(query: str, num_results: int) -> List[str]:
    """Search using DuckDuckGo API endpoint"""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=num_results, backend="api"):
                if isinstance(r, dict) and "link" in r:
                    results.append(
                        {
                            "url": r["link"],
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                        }
                    )
            return results
    except Exception as e:
        logger.error(f"DDG API search error: {e}")
        return []


async def score_and_filter_results(
    query: str,
    results: List[Dict],
    whitelist: List[str] = None,
    blacklist: List[str] = None,
) -> List[SearchResult]:
    """Score and filter search results"""
    try:
        keywords = query.lower().split()
        scored_results = []
        seen_domains = set()

        for result in results:
            try:
                url = result.get("url")
                if not url:
                    continue

                domain = urlparse(url).netloc.lower()

                # Skip if we've seen this domain with a higher score
                if domain in seen_domains:
                    continue

                # Apply whitelist/blacklist filters
                if whitelist and not any(domain.endswith(w.lower()) for w in whitelist):
                    continue
                if blacklist and any(domain.endswith(b.lower()) for b in blacklist):
                    continue

                # Calculate score
                score = calculate_score(url, domain, keywords)

                # Add to results if score is positive
                if score > 0:
                    seen_domains.add(domain)
                    scored_results.append(
                        SearchResult(
                            url=url,
                            title=result.get("title", url),
                            content=result.get("snippet", ""),
                            score=score,
                            metadata=result.get("metadata", {}),
                        )
                    )

            except Exception as e:
                logger.error(f"Error processing result {url}: {str(e)}")
                continue

        # Sort by score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results

    except Exception as e:
        logger.error(f"Scoring error: {str(e)}")
        return []


def calculate_score(url: str, domain: str, keywords: List[str]) -> float:
    """Calculate relevance score for a URL"""
    score = 0
    url_lower = url.lower()

    for keyword in keywords:
        # Domain matches (highest weight)
        if keyword in domain:
            score += 2
        # URL path matches (lower weight)
        elif keyword in url_lower:
            score += 1

    return score

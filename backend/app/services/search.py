from typing import List, Dict, Set, Optional, Any
from urllib.parse import urlparse
import logging
import os
from ..config import settings
from ..models import SearchResult
from googlesearch import search as gsearch
from duckduckgo_search import DDGS
import asyncio
from ..utils.domain import check_domain_lists, is_domain_match
import re
from asyncio import Semaphore
import random
import json

logger = logging.getLogger(__name__)

# Define common words as a module-level constant
COMMON_WORDS = {
    "the",
    "and",
    "or",
    "in",
    "at",
    "of",
    "to",
    "for",
    "a",
    "an",
    "center",
    "clinic",
    "hospital",
    "medical",
    "health",
    "healthcare",
    "services",
    "care",
    "treatment",
    "facility",
}

# Create a semaphore to limit concurrent searches
SEARCH_SEMAPHORE = Semaphore(2)  # Allow 2 concurrent searches


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


def is_domain_match(domain: str, pattern: str) -> bool:
    """
    Check if a domain matches a pattern, handling www and subdomains.
    Example matches:
    - example.com matches example.com
    - www.example.com matches example.com
    - sub.example.com matches example.com
    - example.com matches www.example.com
    """
    try:
        # Clean up domains
        domain = domain.lower().strip()
        pattern = pattern.lower().strip()

        # Remove www.
        domain = domain.replace("www.", "")
        pattern = pattern.replace("www.", "")

        # Direct match
        if domain == pattern:
            return True

        # Check if domain is a subdomain of pattern
        if domain.endswith("." + pattern):
            return True

        # Check if pattern is a subdomain of domain
        if pattern.endswith("." + domain):
            return True

        return False
    except Exception as e:
        logger.error(f"Error in domain matching: {e}")
        return False


def is_official_site(domain: str, org_name: str, significant_words: List[str]) -> float:
    """
    Enhanced domain matching logic to handle various naming patterns.
    Returns a confidence score between 0 and 1.
    """
    try:
        # Clean domain and org name
        clean_domain = domain.lower().replace("www.", "")
        base_domain = clean_domain.split(".")[0]
        org_name_lower = org_name.lower()

        logger.info(f"\nAnalyzing domain: {clean_domain}")
        logger.info(f"Organization: {org_name_lower}")
        logger.info(f"Significant words: {significant_words}")

        # Split domain parts (handle hyphens, numbers, etc)
        domain_parts = set(re.split(r"[-._]", base_domain))
        logger.info(f"Domain parts: {domain_parts}")

        # Generate organization name variations
        name_parts = org_name_lower.split()

        # Initialize word_ratio
        word_ratio = 0.0

        # Generate acronym variations
        acronyms = set()

        # Full acronym from all words (e.g., "WHRC" from "WHRC West Hollywood Recovery Center")
        full_acronym = "".join(word[0] for word in name_parts)
        acronyms.add(full_acronym)

        # Full acronym without common words
        filtered_acronym = "".join(
            word[0] for word in name_parts if word not in COMMON_WORDS
        )
        acronyms.add(filtered_acronym)

        # Handle cases where org name starts with its acronym
        first_word = name_parts[0].upper()
        if len(first_word) <= 5:  # Likely an acronym
            acronyms.add(first_word.lower())

        # Consecutive word acronyms (e.g., "wh" from "West Hollywood")
        for i in range(len(name_parts) - 1):
            if name_parts[i] not in COMMON_WORDS:
                # Two-word acronyms
                if name_parts[i + 1] not in COMMON_WORDS:
                    acronyms.add(name_parts[i][0] + name_parts[i + 1][0])
                # Three-word acronyms if available
                if i + 2 < len(name_parts) and name_parts[i + 2] not in COMMON_WORDS:
                    acronyms.add(
                        name_parts[i][0] + name_parts[i + 1][0] + name_parts[i + 2][0]
                    )

        logger.info(f"Generated acronyms: {acronyms}")

        # Check for exact acronym match, including with "the" prefix
        for acronym in acronyms:
            if base_domain == f"the{acronym.lower()}":
                logger.info(f"Found exact acronym match with 'the' prefix: {acronym}")
                return 1.0
            if acronym.lower() == base_domain:
                logger.info(f"Found exact acronym match: {acronym}")
                return 1.0
            if acronym.lower() in domain_parts:
                logger.info(f"Found acronym in domain parts: {acronym}")
                return 0.9

        # Calculate word matches with consecutive word bonus
        consecutive_matches = 0
        for i in range(len(significant_words) - 1):
            if (
                significant_words[i] in base_domain
                and significant_words[i + 1] in base_domain
            ):
                consecutive_matches += 1

        # Calculate basic word ratio
        matching_words = sum(1 for word in significant_words if word in base_domain)
        word_ratio = matching_words / len(significant_words) if significant_words else 0

        # Add bonus for consecutive word matches
        if consecutive_matches > 0:
            word_ratio = min(1.0, word_ratio + (0.2 * consecutive_matches))
            logger.info(f"Found {consecutive_matches} consecutive word matches")

        # Check for healthcare-related terms at start or end of domain
        healthcare_terms = {
            "mhr": 0.8,
            "mhc": 0.8,
            "bhc": 0.7,
            "rc": 0.7,
            "health": 0.6,
            "recovery": 0.6,
            "rehab": 0.6,
        }

        # Need to modify this to handle compound terms
        for term, weight in healthcare_terms.items():
            # Current logic is too restrictive
            if base_domain.startswith(term) or base_domain.endswith(term):
                word_ratio = max(word_ratio, weight)
                logger.info(f"Found healthcare term at boundary: {term}")

        logger.info(f"Final word ratio: {word_ratio}")
        return word_ratio

    except Exception as e:
        logger.error(f"Error in official site check: {e}")
        return 0.0


async def process_search_results(
    query: str,
    results: List[Dict],
    whitelist: List[str] = None,
    blacklist: List[str] = None,
    min_score: float = None,
) -> List[Dict]:
    """Process search results prioritizing official website and whitelisted domains"""
    try:
        # Parse organization name and location from query
        parts = query.split("-")
        org_name = parts[0].strip()
        location = parts[1].strip() if len(parts) > 1 else ""

        # Get significant words from org name
        significant_words = [
            word.lower()
            for word in org_name.split()
            if word.lower() not in COMMON_WORDS and len(word) > 2
        ]

        logger.info(f"Significant words from query: {significant_words}")
        logger.info(f"Location: {location}")

        # Process and categorize results
        final_results = []
        whitelisted_sites = []
        seen_domains = set()  # Track all unique domains
        official_site_found = False

        for result in results:
            try:
                url = result.get("url", "")
                if not url:
                    continue

                domain = urlparse(url).netloc.lower()
                base_domain = ".".join(domain.replace("www.", "").split(".")[-2:])

                # Skip blacklisted domains
                if blacklist and any(is_domain_match(domain, b) for b in blacklist):
                    logger.info(f"Skipping blacklisted domain: {domain}")
                    continue

                # If we haven't found an official site yet, check if this is one
                if not official_site_found:
                    official_score = is_official_site(
                        domain, org_name.split("-")[0], significant_words
                    )

                    if official_score >= 0.5:
                        result["is_official"] = True
                        result["official_score"] = official_score
                        final_results.append(result)
                        seen_domains.add(base_domain)
                        official_site_found = True
                        logger.info(
                            f"Found official site: {domain} (score: {official_score})"
                        )
                        continue

                # Check for whitelist match if not official site
                if whitelist:
                    is_whitelisted = any(is_domain_match(domain, w) for w in whitelist)
                    if is_whitelisted:
                        result["is_official"] = False
                        whitelisted_sites.append(result)
                        logger.info(f"Found whitelisted site: {domain}")

            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
                continue

        search_settings = await settings.get_search_settings()
        scrape_limit = search_settings["SCRAPE_LIMIT"]

        # Add whitelisted sites up to scrape limit, considering domain diversity
        remaining_slots = scrape_limit - len(seen_domains)

        if remaining_slots > 0:
            for site in whitelisted_sites:
                domain = urlparse(site["url"]).netloc.lower().replace("www.", "")
                base_domain = ".".join(domain.split(".")[-2:])

                if base_domain not in seen_domains and len(seen_domains) < scrape_limit:
                    final_results.append(site)
                    seen_domains.add(base_domain)
                    logger.info(f"Added whitelisted domain: {base_domain}")

        logger.info(f"Final results count: {len(final_results)}")
        logger.info(f"Final unique domains: {seen_domains}")
        return final_results

    except Exception as e:
        logger.error(f"Error processing results: {str(e)}")
        return []


async def perform_search(
    query: str,
    whitelist: List[str] = None,
    blacklist: List[str] = None,
    limit: int = None,
    min_score: float = None,
) -> List[Dict]:
    """Main search function that orchestrates the entire search process."""
    try:
        # Get settings from DB
        search_settings = await settings.get_search_settings()

        # Get lists from DB
        from ..models.settings import WhitelistDomain, BlacklistDomain

        db_whitelist = await WhitelistDomain.get_all_domains()
        db_blacklist = await BlacklistDomain.get_all_domains()

        # Combine lists from request and DB
        combined_whitelist = list(set((whitelist or []) + db_whitelist))
        combined_blacklist = list(set((blacklist or []) + db_blacklist))

        logger.info(f"Combined whitelist: {combined_whitelist}")
        logger.info(f"Combined blacklist: {combined_blacklist}")

        # Use provided limits or fall back to settings
        search_limit = limit or search_settings.get(
            "SEARCH_RESULTS_LIMIT", settings.SEARCH_RESULTS_LIMIT
        )
        score_threshold = min_score or search_settings.get(
            "MIN_SCORE_THRESHOLD", settings.MIN_SCORE_THRESHOLD
        )

        # Get raw search results
        raw_results = await get_search_results(query, num_results=search_limit)

        # Process and score results with combined lists
        processed_results = await process_search_results(
            query=query,
            results=raw_results,
            whitelist=combined_whitelist,
            blacklist=combined_blacklist,
            min_score=score_threshold,
        )

        return processed_results[:search_limit]

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise


async def get_search_results(query: str, num_results: int) -> List[Dict]:
    """Get search results with rate limiting"""
    async with SEARCH_SEMAPHORE:
        try:
            # Try Google first with random delay between requests
            results = await google_search(query, num_results)

            if results:
                logger.info("Using Google search results")
                return results

            # Fallback to DuckDuckGo if Google fails
            logger.info("No Google results, falling back to DuckDuckGo")
            return await perform_ddg_search(query, num_results)

        except Exception as e:
            logger.error(f"Search provider error: {str(e)}")
            return []


async def google_search(query: str, num_results: int) -> List[Dict]:
    """Perform Google search with random delays between requests"""
    try:
        results = []
        for result in gsearch(
            query,
            num=num_results,
            lang="en",
            country="US",
            stop=num_results,
            pause=random.uniform(1.0, 3.0),  # Random delay between 1-3 seconds
        ):
            if result:
                results.append(
                    {
                        "url": result,
                        "title": result,
                        "snippet": "",
                        "score": 0,
                    }
                )
                # Add additional random delay between results
                # await asyncio.sleep(random.uniform(1.0, 3.0))

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


class SearchService:
    def __init__(self):
        self.logs_dir = os.environ.get("LOGS_DIR", "logs")

    async def get_log(self, process_id: str) -> Optional[Dict[str, Any]]:
        try:
            log_path = os.path.join(self.logs_dir, f"{process_id}.json")
            if not os.path.exists(log_path):
                return None

            with open(log_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting log {process_id}: {str(e)}")
            return None

    async def get_child_logs(self, parent_process_id: str) -> List[Dict[str, Any]]:
        try:
            child_logs = []
            # List all log files in the directory
            for filename in os.listdir(self.logs_dir):
                if not filename.endswith(".json"):
                    continue

                file_path = os.path.join(self.logs_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        log_data = json.load(f)
                        # Check if this is a child log of the parent
                        if log_data.get("parent_process_id") == parent_process_id:
                            child_logs.append(log_data)
                except Exception as e:
                    logger.error(f"Error reading log file {filename}: {str(e)}")
                    continue

            return sorted(
                child_logs, key=lambda x: x.get("timestamp", ""), reverse=True
            )
        except Exception as e:
            logger.error(f"Error getting child logs for {parent_process_id}: {str(e)}")
            return []

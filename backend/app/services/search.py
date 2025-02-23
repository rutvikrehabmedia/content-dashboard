from typing import List, Dict
from urllib.parse import urlparse
import logging
import os

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

        # 1. Domain match
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

        final_score = max(0.0, min(1.0, score))

        # Log detailed breakdown
        logger.info("\nScore breakdown:")
        for detail in score_breakdown:
            logger.info(f"- {detail}")
        logger.info(f"Final score: {final_score:.2f}")
        logger.info("=" * 50)

        return final_score

    except Exception as e:
        logger.error(f"Error calculating score for {url}: {str(e)}")
        logger.exception(e)
        return 0.0


def process_search_results(query: str, results: List[Dict]) -> List[Dict]:
    """Process search results to add relevance scores and limit results"""
    logger.info(f"\nProcessing {len(results)} search results")

    scored_results = []
    for i, result in enumerate(results, 1):
        logger.info(f"\nProcessing result {i}/{len(results)}")
        score = calculate_relevance_score(query, result)
        result["score"] = score
        scored_results.append(result)

    # Sort by score in descending order
    scored_results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Get top N results
    max_results = int(os.getenv("MAX_RESULTS_PER_QUERY", 2))
    final_results = scored_results[:max_results]

    logger.info("\nFinal Results:")
    for i, result in enumerate(final_results, 1):
        logger.info(f"{i}. {result['url']} - Score: {result['score']:.2f}")

    return final_results

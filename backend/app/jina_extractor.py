import aiohttp
from typing import Dict
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

class JinaExtractor:
    def __init__(self):
        self.headers = {
            "X-API-Key": "jina_543326a7cc8648629fc35bf4a91f5cdcuL1yoTIaHk-LFlaiDQkur9-tXcIk",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def extract_content(self, url: str) -> Dict:
        """Extract content using Jina Reader API"""
        try:
            # Properly encode the URL for the API request
            encoded_url = urllib.parse.quote(url, safe="")
            api_url = f"https://r.jina.ai/{encoded_url}"

            logger.info(f"Processing URL: {url}")
            logger.info(f"API URL: {api_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status != 200:
                        error_msg = f"API returned status code {response.status}"
                        logger.error(error_msg)
                        return {
                            "status": "error",
                            "error": error_msg,
                            "url": url,
                        }

                    data = await response.json()

                    # Check for error in response
                    if data.get("code") != 200:
                        error_msg = f"API error: {data.get('status', 'Unknown error')}"
                        logger.error(error_msg)
                        return {"status": "error", "error": error_msg, "url": url}

                    # Extract content from response
                    if "data" in data:
                        content = data["data"].get("content", "")
                        if not content:
                            logger.warning(f"No content extracted from {url}")

                        result = {
                            "status": "success",
                            "content": content,
                            "metadata": {
                                "title": data["data"].get("title", ""),
                                "description": data["data"].get("description", ""),
                                "url": url,
                                "word_count": len(content.split()) if content else 0,
                                "sentence_count": len(content.split(".")) if content else 0,
                                "language": data["data"].get("language", "en"),
                                "author": data["data"].get("author", ""),
                                "published_date": data["data"].get("published_date", ""),
                                "extraction_method": "jina_reader",
                            },
                        }

                        logger.info(f"Successfully extracted {len(content)} characters from {url}")
                        return result
                    else:
                        error_msg = f"Unexpected response format: {data}"
                        logger.error(error_msg)
                        return {"status": "error", "error": error_msg, "url": url}

        except Exception as e:
            error_msg = f"Extraction error for {url}: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg, "url": url}

    async def close(self):
        """No cleanup needed for API client"""
        pass 
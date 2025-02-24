from typing import Dict, Optional
import re


class BlockDetector:
    BLOCK_PATTERNS = [
        # Cloudflare
        r"cloudflare|please wait|ddos protection|security check",
        # Generic captcha
        r"captcha|robot check|verify you're human",
        # Access denied patterns
        r"access denied|forbidden|blocked|rate limited|too many requests",
        # Empty or minimal content
        r"^(\s*|.{0,50})$",  # Empty or very short content
    ]

    @staticmethod
    def is_blocked(
        response_text: str, status_code: int, headers: Dict
    ) -> tuple[bool, Optional[str]]:
        """
        Detect if the response indicates blocking
        Returns: (is_blocked, reason)
        """
        # Check status codes
        if status_code in [403, 429, 503]:
            return True, f"Blocked status code: {status_code}"

        # Check for empty content
        if not response_text or len(response_text.strip()) < 50:
            return True, "Empty or minimal content"

        # Check for block patterns in content
        text_lower = response_text.lower()
        for pattern in BlockDetector.BLOCK_PATTERNS:
            if re.search(pattern, text_lower):
                return True, f"Blocked pattern detected: {pattern}"

        # Check headers for rate limiting
        rate_limit_remaining = headers.get("x-ratelimit-remaining", "").strip()
        if rate_limit_remaining and rate_limit_remaining == "0":
            return True, "Rate limit exceeded"

        return False, None

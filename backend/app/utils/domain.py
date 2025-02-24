from urllib.parse import urlparse
from typing import List

def normalize_domain(domain: str) -> str:
    """Normalize domain by removing www. and converting to lowercase"""
    return domain.lower().replace('www.', '')

def is_domain_match(url: str, domain_pattern: str) -> bool:
    """
    Check if URL matches domain pattern, considering subdomains
    Example: 
    - url: "https://sub.example.com"
    - pattern: "example.com" -> True
    - pattern: "sub.example.com" -> True
    - pattern: "other.com" -> False
    """
    try:
        domain = normalize_domain(urlparse(url).netloc)
        pattern = normalize_domain(domain_pattern)
        
        # Direct match
        if domain == pattern:
            return True
            
        # Subdomain match
        if domain.endswith('.' + pattern):
            return True
            
        return False
    except:
        return False

def check_domain_lists(url: str, whitelist: List[str] = None, blacklist: List[str] = None) -> bool:
    """Check if URL matches whitelist/blacklist rules"""
    if not url:
        return False
        
    # If whitelist exists, URL must match at least one whitelist domain
    if whitelist:
        if not any(is_domain_match(url, pattern) for pattern in whitelist):
            return False
            
    # If blacklist exists, URL must not match any blacklist domain
    if blacklist:
        if any(is_domain_match(url, pattern) for pattern in blacklist):
            return False
            
    return True 
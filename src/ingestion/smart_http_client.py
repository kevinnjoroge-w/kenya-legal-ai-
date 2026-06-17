"""
Kenya Legal AI — Smart HTTP Client
==================================
Robust HTTP client with adaptive rate limiting, user-agent rotation, 
and intelligent error handling to prevent 403 and 404 errors.
"""

import asyncio
import logging
import random
import time
from typing import Dict, Optional, Any, List
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

# --- Configuration & Constants ---

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

DEFAULT_DOMAIN_LIMITS = {
    "kenyalaw.org": (2.5, 2, 1.8),      # (base_delay, concurrency, multiplier)
    "new.kenyalaw.org": (3.0, 1, 2.0),
    "judiciary.go.ke": (2.0, 2, 1.5),
    "parliament.go.ke": (2.0, 2, 1.5),
}

class AdaptiveRateLimiter:
    """Adaptive rate limiter with exponential backoff and per-domain tracking."""
    
    def __init__(self, domain_limits: Optional[Dict] = None):
        self.limits = domain_limits or DEFAULT_DOMAIN_LIMITS
        self.domain_failures: Dict[str, int] = {}
        self.last_request_time: Dict[str, float] = {}
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    async def get_semaphore(self, domain: str) -> asyncio.Semaphore:
        """Get or create a semaphore for a specific domain."""
        async with self._lock:
            if domain not in self.semaphores:
                concurrency = self.limits.get(domain, (2.0, 2, 1.5))[1]
                self.semaphores[domain] = asyncio.Semaphore(concurrency)
            return self.semaphores[domain]

    def get_delay(self, domain: str) -> float:
        """Calculate the required delay for a domain based on failure history."""
        base_delay, _, multiplier = self.limits.get(domain, (2.0, 2, 1.5))
        failures = self.domain_failures.get(domain, 0)
        
        # Exponential backoff: base_delay * (multiplier ** failures)
        delay = base_delay * (multiplier ** failures)
        
        # Add jitter: 0.8–1.2x multiplier
        jitter = random.uniform(0.8, 1.2)
        return delay * jitter

    async def wait(self, domain: str):
        """Wait for the required delay before the next request to a domain."""
        delay = self.get_delay(domain)
        last_time = self.last_request_time.get(domain, 0)
        elapsed = time.time() - last_time
        
        wait_time = max(0, delay - elapsed)
        if wait_time > 0:
            logger.debug(f"Waiting {wait_time:.2f}s for domain {domain} (failures: {self.domain_failures.get(domain, 0)})")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()

    def record_success(self, domain: str):
        """Reset failure count on success."""
        self.domain_failures[domain] = 0

    def record_failure(self, domain: str, status_code: int):
        """Increase failure count on specific errors."""
        if status_code in (403, 429, 503, 502):
            self.domain_failures[domain] = self.domain_failures.get(domain, 0) + 1
            logger.warning(f"Recorded failure ({status_code}) for {domain}. Failures: {self.domain_failures[domain]}")

class SmartHTTPClient:
    """Robust HTTP client with connection pooling, retries, and rate limiting."""
    
    def __init__(
        self, 
        max_connections: int = 10, 
        max_keepalive: int = 5,
        timeout: float = 30.0
    ):
        limits = httpx.Limits(
            max_keepalive_connections=max_keepalive,
            max_connections=max_connections
        )
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            http2=True,
            verify=False  # Some Kenyan gov sites have SSL issues
        )
        self.rate_limiter = AdaptiveRateLimiter()
        self.stats = {
            "success": 0,
            "403_errors": 0,
            "404_errors": 0,
            "429_errors": 0,
            "timeouts": 0,
            "others": 0
        }

    async def close(self):
        await self.client.aclose()

    def _get_headers(self, attempt: int) -> Dict[str, str]:
        """Generate randomized headers for each attempt."""
        return {
            "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation to prevent junk requests."""
        if not url or len(url) > 2000:
            return False
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        if url.count("//") > 3:
            return False
        return True

    async def fetch(self, url: str, method: str = "GET", **kwargs) -> Optional[httpx.Response]:
        """Fetch a URL with adaptive rate limiting and intelligent retries."""
        if not self._is_valid_url(url):
            logger.warning(f"Skipping invalid or suspicious URL: {url}")
            return None

        domain = urlparse(url).netloc
        semaphore = await self.rate_limiter.get_semaphore(domain)

        async with semaphore:
            for attempt in range(4):  # Up to 4 attempts
                await self.rate_limiter.wait(domain)
                
                headers = self._get_headers(attempt)
                if "headers" in kwargs:
                    headers.update(kwargs["headers"])
                
                try:
                    response = await self.client.request(
                        method, url, headers=headers, **{k: v for k, v in kwargs.items() if k != "headers"}
                    )
                    
                    if response.status_code == 200:
                        self.rate_limiter.record_success(domain)
                        self.stats["success"] += 1
                        return response
                    
                    if response.status_code == 404:
                        logger.warning(f"404 Not Found: {url}")
                        self.stats["404_errors"] += 1
                        return response  # Don't retry 404
                    
                    if response.status_code == 403:
                        logger.warning(f"403 Forbidden for {url} (Attempt {attempt+1})")
                        self.stats["403_errors"] += 1
                        self.rate_limiter.record_failure(domain, 403)
                    
                    elif response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 30
                        logger.warning(f"429 Too Many Requests for {url}. Waiting {wait_time}s...")
                        self.stats["429_errors"] += 1
                        self.rate_limiter.record_failure(domain, 429)
                        await asyncio.sleep(wait_time)
                    
                    elif response.status_code >= 500:
                        logger.warning(f"{response.status_code} Server Error for {url} (Attempt {attempt+1})")
                        self.rate_limiter.record_failure(domain, response.status_code)
                    
                    if attempt == 3:
                        return response

                except httpx.TimeoutException:
                    logger.warning(f"Timeout for {url} (Attempt {attempt+1})")
                    self.stats["timeouts"] += 1
                    if attempt == 3: raise
                except httpx.NetworkError:
                    logger.warning(f"Network error for {url} (Attempt {attempt+1})")
                    if attempt == 3: raise
                except Exception as e:
                    logger.error(f"Unexpected error fetching {url}: {e}")
                    self.stats["others"] += 1
                    if attempt == 3: raise

        return None

    def get_stats(self) -> Dict[str, int]:
        return self.stats

# Global client instance to ensure connection pooling
_global_client: Optional[SmartHTTPClient] = None

def get_http_client() -> SmartHTTPClient:
    global _global_client
    if _global_client is None:
        _global_client = SmartHTTPClient()
    return _global_client

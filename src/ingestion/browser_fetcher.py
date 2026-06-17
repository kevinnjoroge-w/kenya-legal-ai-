"""
Kenya Legal AI — Browser-backed HTML fetcher
===========================================

This helper uses browser-use-sdk v3 to fetch fully rendered HTML for pages that
require browser execution or client-side JavaScript.
"""

import logging
from typing import Optional

from browser_use_sdk.v3.client import AsyncBrowserUse

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class BrowserUseFetcher:
    """Fetch rendered HTML using browser-use-sdk v3."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.browser_use_api_key or None
        self.base_url = settings.browser_use_base_url or None
        self.timeout = settings.browser_use_timeout
        self.default_model = settings.browser_use_model or None

    async def fetch_html(
        self,
        url: str,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Fetch a page with browser rendering and return the final HTML."""
        if not self.api_key:
            raise ValueError(
                "BrowserUseFetcher requires BROWSER_USE_API_KEY to be set."
            )

        browser = AsyncBrowserUse(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout or self.timeout,
        )

        task = (
            "Load the current browser session page and return the final rendered "
            "HTML exactly as plain text. Do not include any commentary, markdown, "
            "JSON wrappers, or additional explanation."
        )

        try:
            result = await browser.run(
                task,
                model=model or self.default_model,
                max_cost_usd=2.0,
                session_settings={
                    "initialUrl": url,
                    "keepAlive": False,
                },
            )
            html = result.output
            if html is None:
                raise RuntimeError("BrowserUse returned no HTML content.")
            return str(html).strip()

        finally:
            await browser.close()

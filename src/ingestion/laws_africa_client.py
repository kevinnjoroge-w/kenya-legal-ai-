"""
Kenya Legal AI — Laws.Africa API Client
========================================
Fetches Kenyan legislation from the Laws.Africa Content API v3.
Supports fetching legislation listings, full text in Akoma Ntoso XML, and HTML.

API Docs: https://developers.laws.africa/
"""

import json
import logging
from pathlib import Path
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

KENYA_COUNTRY_CODE = "ke"


class LawsAfricaClient:
    """Client for the Laws.Africa Content API v3."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.laws_africa_base_url.rstrip("/")
        self.api_key = settings.laws_africa_api_key
        self.raw_data_dir = Path(settings.raw_data_dir) / "laws_africa"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            logger.warning(
                "LAWS_AFRICA_API_KEY not set. "
                "Get one at https://developers.laws.africa/"
            )

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self.api_key}",
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """Make an authenticated GET request to the API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _get_text(self, url: str, accept: str = "text/html") -> str:
        """Make a GET request and return the text content."""
        headers = {**self._headers, "Accept": accept}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    async def list_works(
        self,
        year: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """
        List all legislative works for Kenya.

        Args:
            year: Filter by year of publication
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            API response with list of legislative works
        """
        url = f"{self.base_url}/akn/{KENYA_COUNTRY_CODE}/.json"
        params = {"page": page, "page_size": page_size}
        if year:
            params["year"] = year

        logger.info(f"Fetching Kenya legislation list (page={page}, year={year})")
        return await self._get(url, params)

    async def get_work(self, frbr_uri: str) -> dict:
        """
        Get metadata for a specific legislative work.

        Args:
            frbr_uri: FRBR URI of the work (e.g., '/akn/ke/act/2010/constitution')

        Returns:
            Work metadata as JSON
        """
        url = f"{self.base_url}{frbr_uri}/.json"
        logger.info(f"Fetching work: {frbr_uri}")
        return await self._get(url)

    async def get_work_html(self, frbr_uri: str) -> str:
        """
        Get the full HTML content of a legislative work.

        Args:
            frbr_uri: FRBR URI of the work

        Returns:
            HTML content of the work
        """
        url = f"{self.base_url}{frbr_uri}/.html"
        logger.info(f"Fetching HTML for: {frbr_uri}")
        return await self._get_text(url, accept="text/html")

    async def get_work_xml(self, frbr_uri: str) -> str:
        """
        Get the Akoma Ntoso XML content of a legislative work.

        Args:
            frbr_uri: FRBR URI of the work

        Returns:
            Akoma Ntoso XML content
        """
        url = f"{self.base_url}{frbr_uri}/.xml"
        logger.info(f"Fetching XML for: {frbr_uri}")
        return await self._get_text(url, accept="application/xml")

    async def fetch_all_kenya_legislation(self) -> list[dict]:
        """
        Fetch all Kenyan legislation metadata, handling pagination.

        Returns:
            List of all legislative work metadata dictionaries
        """
        all_works = []
        page = 1

        while True:
            response = await self.list_works(page=page)
            results = response.get("results", [])
            all_works.extend(results)

            logger.info(
                f"Page {page}: fetched {len(results)} works "
                f"(total: {len(all_works)})"
            )

            # Check for next page
            if response.get("next"):
                page += 1
            else:
                break

        logger.info(f"Total Kenya legislation works fetched: {len(all_works)}")
        return all_works

    # FRBR URI for the Constitution of Kenya 2010
    CONSTITUTION_FRBR_URI = "/akn/ke/act/2010/constitution"

    async def download_constitution(self) -> dict:
        """
        Explicitly download the Constitution of Kenya (2010).

        This is a convenience wrapper around download_work() that targets the
        Constitution by its well-known FRBR URI and saves it under a clearly
        named directory so it is easy to locate in the raw data store.

        Returns:
            Dictionary with metadata and file paths for the Constitution.
        """
        logger.info("Downloading Constitution of Kenya 2010...")
        result = await self.download_work(self.CONSTITUTION_FRBR_URI)
        logger.info("Constitution of Kenya download complete.")
        return result

    async def download_work(self, frbr_uri: str) -> dict:
        """
        Download a legislative work (metadata + HTML content) and save to disk.

        Args:
            frbr_uri: FRBR URI of the work

        Returns:
            Dictionary with metadata and file paths
        """
        # Create safe filename from URI
        safe_name = frbr_uri.strip("/").replace("/", "_")
        work_dir = self.raw_data_dir / safe_name
        work_dir.mkdir(parents=True, exist_ok=True)

        # Fetch metadata
        metadata = await self.get_work(frbr_uri)
        metadata_path = work_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        # Fetch HTML content
        try:
            html_content = await self.get_work_html(frbr_uri)
            html_path = work_dir / "content.html"
            html_path.write_text(html_content, encoding="utf-8")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Could not fetch HTML for {frbr_uri}: {e}")
            html_path = None

        logger.info(f"Downloaded: {frbr_uri} → {work_dir}")

        return {
            "frbr_uri": frbr_uri,
            "metadata_path": str(metadata_path),
            "html_path": str(html_path) if html_path else None,
            "title": metadata.get("title", ""),
        }


async def run_ingestion():
    """Run a full ingestion of Kenya legislation from Laws.Africa."""
    client = LawsAfricaClient()

    # Step 1: Fetch all legislation metadata
    logger.info("Starting Kenya legislation ingestion from Laws.Africa...")
    works = await client.fetch_all_kenya_legislation()

    # Step 2: Save the full listing
    listing_path = client.raw_data_dir / "all_works.json"
    listing_path.write_text(json.dumps(works, indent=2, ensure_ascii=False))
    logger.info(f"Saved work listing to {listing_path}")

    # Step 3: Download each work
    downloaded = []
    for work in works:
        frbr_uri = work.get("frbr_uri", "")
        if frbr_uri:
            try:
                result = await client.download_work(frbr_uri)
                downloaded.append(result)
            except Exception as e:
                logger.error(f"Failed to download {frbr_uri}: {e}")

    logger.info(
        f"Ingestion complete. Downloaded {len(downloaded)}/{len(works)} works."
    )
    return downloaded


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingestion())

"""
Kenya Legal AI — Example Multi-Format Scraper
==============================================
Demonstrates how to build a scraper that uses multi-format support
and deduplication tracking.

This is a template that can be adapted for different sources.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from src.ingestion.scraper_utils import DedupAwareScraper
from src.ingestion.document_handler import DocumentHandler

logger = logging.getLogger(__name__)


class MultiFormatExampleScraper(DedupAwareScraper):
    """
    Example scraper that downloads documents in multiple formats
    and tracks them to prevent duplicates.

    This demonstrates best practices for:
    - Multi-format document support
    - Deduplication tracking
    - Error handling
    - Async operations
    """

    def __init__(self, source_name: str = "example_source"):
        """Initialize the scraper."""
        super().__init__()
        self.source_name = source_name
        self.raw_data_dir = Path("data/raw") / source_name
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.document_handler = DocumentHandler()
        self.logger = logging.getLogger(__name__)

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with error handling."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    async def download_file(self, url: str, save_path: Path) -> Optional[Path]:
        """Download a file to disk."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(response.content)
                return save_path
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return None

    async def scrape_documents(self, search_url: str, limit: int = 10):
        """
        Example: Scrape a search results page and download documents.

        This demonstrates:
        1. Fetching a page with links
        2. Checking for duplicates before downloading
        3. Handling multiple formats
        4. Tracking downloads
        """
        self.logger.info(f"Scraping {search_url} (limit: {limit})")

        # Fetch search results
        html = await self.fetch_page(search_url)
        if not html:
            return

        # Parse links
        soup = BeautifulSoup(html, 'html.parser')
        doc_links = soup.find_all('a', href=True)

        downloaded_count = 0

        for link in doc_links:
            if downloaded_count >= limit:
                break

            doc_url = link.get('href')
            if not doc_url:
                continue

            # Make absolute URL
            if doc_url.startswith('/'):
                base = search_url.split('/')[2]
                doc_url = f"https://{base}{doc_url}"
            elif not doc_url.startswith('http'):
                doc_url = search_url + doc_url

            # Check if already downloaded
            if not self.should_download(doc_url):
                self.logger.debug(f"Skipping already downloaded: {doc_url}")
                continue

            # Download the document
            filename = Path(doc_url).name or f"document_{downloaded_count}"
            save_path = self.raw_data_dir / filename

            self.logger.info(f"Downloading: {doc_url}")
            result = await self.download_file(doc_url, save_path)

            if result:
                # Detect format
                doc_format = self.document_handler.detect_format(result) or "unknown"

                # Mark as downloaded
                self.mark_downloaded(doc_url, result, doc_format)

                self.logger.info(
                    f"Downloaded ({doc_format}): {filename} "
                    f"({result.stat().st_size} bytes)"
                )
                downloaded_count += 1
            else:
                self.logger.warning(f"Failed to download: {doc_url}")

        # Log statistics
        self.logger.info(f"Downloaded {downloaded_count} documents")
        stats = self.get_dedup_stats()
        self.logger.info(f"Dedup stats: {stats}")

    async def extract_and_save_text(self):
        """
        Example: Extract text from all downloaded documents.

        This demonstrates multi-format extraction.
        """
        self.logger.info("Extracting text from all documents...")

        extracted_count = 0
        failed_count = 0

        for doc_path in self.raw_data_dir.iterdir():
            if not doc_path.is_file():
                continue

            # Extract text
            text = self.document_handler.extract_text(doc_path)

            if text:
                # Save text with same name but .txt extension
                text_path = doc_path.with_suffix('.txt')
                text_path.write_text(text, encoding='utf-8')

                self.logger.info(
                    f"Extracted text: {doc_path.name} "
                    f"({len(text)} characters)"
                )
                extracted_count += 1
            else:
                self.logger.warning(f"Failed to extract: {doc_path.name}")
                failed_count += 1

        self.logger.info(
            f"Text extraction complete: "
            f"success={extracted_count}, "
            f"failed={failed_count}"
        )

    async def get_format_statistics(self):
        """Get statistics on downloaded document formats."""
        stats = self.document_handler.get_format_stats(self.raw_data_dir)
        self.logger.info(f"Format statistics: {stats}")
        return stats

    async def ingest_all(self):
        """
        Main ingestion workflow.

        Demonstrates the complete flow:
        1. Download documents with deduplication
        2. Extract text from multiple formats
        3. Report statistics
        """
        self.logger.info(f"Starting ingestion for {self.source_name}")

        try:
            # Step 1: Scrape and download
            await self.scrape_documents(
                search_url="https://example.com/documents",
                limit=20
            )

            # Step 2: Extract text
            await self.extract_and_save_text()

            # Step 3: Report statistics
            format_stats = await self.get_format_statistics()
            dedup_stats = self.get_dedup_stats()

            self.logger.info(f"Ingestion complete for {self.source_name}")
            self.logger.info(f"Format stats: {format_stats}")
            self.logger.info(f"Dedup stats: {dedup_stats}")

        except Exception as e:
            self.logger.error(f"Ingestion failed: {e}", exc_info=True)


async def main():
    """
    Example usage of the MultiFormatExampleScraper.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create scraper instance
    scraper = MultiFormatExampleScraper(source_name="example_documents")

    # Run ingestion
    await scraper.ingest_all()


if __name__ == "__main__":
    # Note: This is just an example. In real usage, you would:
    # 1. Replace the example URL with your actual source
    # 2. Adapt the parsing logic for your specific HTML structure
    # 3. Add more sophisticated error handling as needed
    # 4. Integrate with the mass_ingest orchestrator

    asyncio.run(main())

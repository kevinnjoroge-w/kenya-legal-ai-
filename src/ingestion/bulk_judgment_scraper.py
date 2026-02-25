"""
Kenya Legal AI — Bulk Judgment Scraper
========================================
Orchestrates large-scale ingestion of judgments with checkpointing and concurrency.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.config.settings import get_settings
from src.ingestion.kenya_law_scraper import KenyaLawScraper

logger = logging.getLogger(__name__)

COURT_CATEGORIES = [
    "supreme-court",
    "court-of-appeal",
    "high-court",
    "employment-labour-relations-court",
    "environment-land-court",
    "tribunals",
]

class BulkJudgmentScraper:
    """Manages mass ingestion of judgments with progress tracking."""

    def __init__(self, checkpoint_file: str = "data/metadata/scraping_checkpoint.json"):
        settings = get_settings()
        self.scraper = KenyaLawScraper()
        self.checkpoint_path = Path(checkpoint_file)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint = self._load_checkpoint()
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(10) # Max 5 concurrent page/case fetches

    def _load_checkpoint(self) -> dict:
        """Load progress from disk."""
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text())
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
        
        return {
            "current_category_index": 0,
            "current_page": 1,
            "completed_categories": [],
            "total_scraped": 0,
        }

    def _save_checkpoint(self):
        """Save progress to disk."""
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2))

    async def scrape_page_task(self, court_cat: str, page: int):
        """Scrape all cases on a single page."""
        async with self.semaphore:
            logger.info(f"Scraping {court_cat} - Page {page}")
            cases = await self.scraper.search_cases(court=court_cat, page=page)
            
            if not cases:
                return 0

            count = 0
            for case_info in cases:
                # We skip individual case scraping here to avoid overwhelming in a single loop
                # The search results already give us the basic info.
                # In a real mass ingestion, we'd queue these URLs for full content scraping.
                result = await self.scraper.scrape_case(case_info["url"])
                if result:
                    count += 1
            
            return count

    async def run_bulk_scrape(self, limit_pages: Optional[int] = None):
        """Run the mass ingestion process."""
        start_idx = self.checkpoint["current_category_index"]
        
        for i in range(start_idx, len(COURT_CATEGORIES)):
            court_cat = COURT_CATEGORIES[i]
            logger.info(f"--- Starting Category: {court_cat} ---")
            
            page = self.checkpoint["current_page"] if i == start_idx else 1
            
            while True:
                scraped_on_page = await self.scrape_page_task(court_cat, page)
                
                if scraped_on_page == 0:
                    logger.info(f"Finished category {court_cat}")
                    break
                
                self.checkpoint["total_scraped"] += scraped_on_page
                self.checkpoint["current_page"] = page + 1
                self._save_checkpoint()
                
                page += 1
                
                if limit_pages and page > limit_pages:
                    logger.info(f"Reached limit of {limit_pages} pages.")
                    break
            
            # Reset page for next category
            self.checkpoint["current_page"] = 1
            self.checkpoint["current_category_index"] = i + 1
            if court_cat not in self.checkpoint["completed_categories"]:
                self.checkpoint["completed_categories"].append(court_cat)
            self._save_checkpoint()

        logger.info(f"Bulk scrape complete. Total items: {self.checkpoint['total_scraped']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BulkJudgmentScraper()
    # Test with a small limit first
    asyncio.run(scraper.run_bulk_scrape(limit_pages=10))

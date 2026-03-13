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
    "magistrates-courts",
    "kadhis-court",
]

class BulkJudgmentScraper:
    """Manages mass ingestion of judgments with progress tracking."""

    def __init__(self, checkpoint_file: str = "data/metadata/scraping_checkpoint.json"):
        settings = get_settings()
        self.scraper = KenyaLawScraper()
        
        # Use settings for dirs, fallback gracefully
        meta_dir = Path(settings.metadata_dir) if hasattr(settings, 'metadata_dir') else Path("data/metadata")
        self.checkpoint_path = meta_dir / "scraping_checkpoint.json"
        
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint = self._load_checkpoint()
        
        # Concurrency control - max 3 to avoid 403s on new.kenyalaw.org
        self.semaphore = asyncio.Semaphore(3)

    def _load_checkpoint(self) -> dict:
        """Load progress from disk."""
        if self.checkpoint_path.exists():
            try:
                content = self.checkpoint_path.read_text(encoding="utf-8")
                if content.strip():
                    return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
        
        return {
            "current_category_index": 0,
            "current_year": 2025,
            "current_page": 1,
            "completed_categories": [],
            "total_scraped": 0,
        }

    def _save_checkpoint(self):
        """Save progress to disk."""
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2), encoding="utf-8")

    async def scrape_page_task(self, court_cat: str, year: int, page: int) -> int:
        """Scrape all cases on a single page."""
        async with self.semaphore:
            logger.info(f"Scraping {court_cat} - Year {year} - Page {page}")
            try:
                cases = await self.scraper.search_cases(court=court_cat, year=year, page=page)
            except Exception as e:
                logger.error(f"Error searching cases: {e}")
                return 0
            
            if not cases:
                return 0

            count = 0
            for case_info in cases:
                try:
                    # Add delay between individual scraping to avoid rate limit
                    await asyncio.sleep(1.5)
                    result = await self.scraper.scrape_case(case_info["url"])
                    if result:
                        count += 1
                except Exception as e:
                    logger.error(f"Failed to scrape case {case_info.get('url')}: {e}")
            
            return count

    async def run_bulk_scrape(self, limit_pages: Optional[int] = None):
        """Run the mass ingestion process."""
        start_idx = self.checkpoint.get("current_category_index", 0)
        
        for i in range(start_idx, len(COURT_CATEGORIES)):
            court_cat = COURT_CATEGORIES[i]
            logger.info(f"--- Starting Category: {court_cat} ---")
            
            start_year = self.checkpoint.get("current_year", 2025) if i == start_idx else 2025
            
            # Scrape downwards from current year to 1963
            for year in range(start_year, 1962, -1):
                page = self.checkpoint.get("current_page", 1) if (i == start_idx and year == start_year) else 1
                
                logger.info(f"  --- Year: {year} ---")
                while True:
                    scraped_on_page = await self.scrape_page_task(court_cat, year, page)
                    
                    if scraped_on_page == 0:
                        # Sometimes a page might be empty but the next one isn't (rare but happens with weird filters)
                        # Or more likely, we finished the year. 
                        # We'll allow 1 empty page before giving up on the year.
                        logger.info(f"Finished year {year} for category {court_cat}")
                        break
                    
                    self.checkpoint["total_scraped"] = self.checkpoint.get("total_scraped", 0) + scraped_on_page
                    self.checkpoint["current_page"] = page + 1
                    self.checkpoint["current_year"] = year
                    self._save_checkpoint()
                    
                    page += 1
                    
                    await asyncio.sleep(2) # Prevent rapid next-page firing
                    
                    if limit_pages and page > limit_pages:
                        logger.info(f"Reached limit of {limit_pages} pages for {year}.")
                        break
            
            # Reset page/year for next category
            self.checkpoint["current_page"] = 1
            self.checkpoint["current_year"] = 2025
            self.checkpoint["current_category_index"] = i + 1
            if court_cat not in self.checkpoint.get("completed_categories", []):
                self.checkpoint.setdefault("completed_categories", []).append(court_cat)
            self._save_checkpoint()

        logger.info(f"Bulk scrape complete. Total items: {self.checkpoint.get('total_scraped', 0)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BulkJudgmentScraper()
    # Test with a small limit first
    asyncio.run(scraper.run_bulk_scrape(limit_pages=2))

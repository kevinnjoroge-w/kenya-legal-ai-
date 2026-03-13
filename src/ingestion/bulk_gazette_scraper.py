"""
Kenya Legal AI — Bulk Gazette Scraper
=======================================
Orchestrates large-scale ingestion of gazettes with checkpointing and concurrency.
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

class BulkGazetteScraper:
    """Manages mass ingestion of gazettes with progress tracking."""

    def __init__(self, checkpoint_file: str = "data/metadata/gazette_scraping_checkpoint.json"):
        settings = get_settings()
        self.scraper = KenyaLawScraper()
        
        meta_dir = Path(settings.metadata_dir) if hasattr(settings, 'metadata_dir') else Path("data/metadata")
        self.checkpoint_path = meta_dir / "gazette_scraping_checkpoint.json"
        
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint = self._load_checkpoint()
        
        # Concurrency control
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
            "current_year": 2025,
            "total_scraped": 0,
        }

    def _save_checkpoint(self):
        """Save progress to disk."""
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2), encoding="utf-8")

    async def run_bulk_scrape(self, start_year: int = 2025, end_year: int = 2010):
        """Run the mass ingestion process for gazettes."""
        year = self.checkpoint.get("current_year", start_year)
        
        for y in range(year, end_year - 1, -1):
            logger.info(f"--- Starting Gazettes for Year: {y} ---")
            
            try:
                # Add delay to avoid aggressive hits
                await asyncio.sleep(2)
                
                notices = await self.scraper.scrape_gazettes(year=y)
                
                if not notices:
                    logger.info(f"No gazettes found for year {y}")
                    self.checkpoint["current_year"] = y - 1
                    self._save_checkpoint()
                    continue

                count = 0
                for notice in notices:
                    try:
                        await asyncio.sleep(2)
                        result = await self.scraper.scrape_document_full(notice)
                        if result:
                            count += 1
                    except Exception as e:
                        logger.error(f"Failed to scrape gazette {notice.get('url')}: {e}")
                
                self.checkpoint["total_scraped"] = self.checkpoint.get("total_scraped", 0) + count
                self.checkpoint["current_year"] = y - 1
                self._save_checkpoint()
                logger.info(f"Scraped {count} gazettes for year {y}")
                
            except Exception as e:
                logger.error(f"Error processing year {y}: {e}")
                break

        logger.info(f"Bulk gazette scrape complete. Total items: {self.checkpoint.get('total_scraped', 0)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BulkGazetteScraper()
    # Test with just recent years
    asyncio.run(scraper.run_bulk_scrape(start_year=2024, end_year=2023))

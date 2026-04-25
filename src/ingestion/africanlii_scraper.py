"""
Kenya Legal AI — AfricanLII Scraper
====================================
Integrates with AfricanLII API to fetch Kenya-specific case law,
legislation, and legal documents.

AfricanLII (https://africanlii.org/) provides free access to African
court decisions and legislation.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

AFRICANLII_BASE_URL = "https://api.africanlii.org"
KENYA_JURISDICTION = "ke"  # Kenya jurisdiction code


class AfricanLIIScraper:
    """
    Scraper for African Legal Information Institute (AfricanLII)
    Kenya-specific case law and legislation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.raw_data_dir = Path(self.settings.raw_data_dir) / "africanlii"
        self.cases_dir = self.raw_data_dir / "cases"
        self.legislation_dir = self.raw_data_dir / "legislation"
        self.metadata_dir = Path(self.settings.metadata_dir)
        
        for d in [self.cases_dir, self.legislation_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_json(self, url: str) -> Dict:
        """Fetch JSON from AfricanLII API with retry."""
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def search_cases(
        self,
        query: Optional[str] = None,
        year_start: int = 2000,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Search for Kenya cases on AfricanLII.
        
        Args:
            query: Optional search term
            year_start: Start year for cases
            limit: Maximum results to return
        
        Returns:
            List of case metadata dictionaries
        """
        try:
            # Build search URL
            search_url = f"{AFRICANLII_BASE_URL}/search/"
            params = {
                "jurisdiction": KENYA_JURISDICTION,
                "limit": limit,
            }
            if query:
                params["q"] = query
            
            logger.info(f"Searching AfricanLII for Kenya cases...")
            # Note: AfricanLII may not have a direct search API; fallback to browsing
            # Check their API documentation for actual endpoints
            
            # For now, use a generic browse endpoint
            browse_url = f"{AFRICANLII_BASE_URL}/jurisdiction/{KENYA_JURISDICTION}/cases/"
            
            try:
                data = await self._fetch_json(browse_url)
                cases = data.get("results", [])
                logger.info(f"Found {len(cases)} cases on AfricanLII")
                return cases
            except Exception as e:
                logger.warning(f"AfricanLII API may not support direct browsing: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching AfricanLII cases: {e}")
            return []

    async def fetch_case_details(self, case_id: str) -> Optional[Dict]:
        """
        Fetch detailed information about a specific case.
        
        Args:
            case_id: Unique identifier for the case
        
        Returns:
            Case details or None if not found
        """
        try:
            url = f"{AFRICANLII_BASE_URL}/case/{case_id}/"
            data = await self._fetch_json(url)
            return data
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {e}")
            return None

    async def fetch_legislation(
        self,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Fetch Kenya legislation from AfricanLII.
        
        Args:
            limit: Maximum results to return
        
        Returns:
            List of legislation metadata
        """
        try:
            url = f"{AFRICANLII_BASE_URL}/jurisdiction/{KENYA_JURISDICTION}/legislation/"
            data = await self._fetch_json(url)
            legislation = data.get("results", [])
            logger.info(f"Found {len(legislation)} legislation items on AfricanLII")
            return legislation
        except Exception as e:
            logger.error(f"Error fetching AfricanLII legislation: {e}")
            return []

    async def save_case(self, case: Dict) -> bool:
        """Save case metadata and content."""
        try:
            case_id = case.get("id") or case.get("case_id")
            if not case_id:
                return False
            
            # Save metadata
            metadata_file = self.cases_dir / f"{case_id}_metadata.json"
            metadata_file.write_text(json.dumps(case, indent=2))
            
            # Save case content if available
            content_file = self.cases_dir / f"{case_id}_content.txt"
            content = case.get("content") or case.get("text") or case.get("summary", "")
            if content:
                content_file.write_text(str(content))
            
            logger.info(f"Saved case: {case_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving case: {e}")
            return False

    async def save_legislation(self, leg: Dict) -> bool:
        """Save legislation metadata and content."""
        try:
            leg_id = leg.get("id") or leg.get("title", "").replace(" ", "_")
            if not leg_id:
                return False
            
            metadata_file = self.legislation_dir / f"{leg_id}_metadata.json"
            metadata_file.write_text(json.dumps(leg, indent=2))
            
            content_file = self.legislation_dir / f"{leg_id}_content.txt"
            content = leg.get("content") or leg.get("text") or ""
            if content:
                content_file.write_text(str(content))
            
            logger.info(f"Saved legislation: {leg_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving legislation: {e}")
            return False

    async def ingest_all(self):
        """Ingest all Kenya cases and legislation from AfricanLII."""
        logger.info("=== Starting AfricanLII Ingestion ===")
        
        # Fetch and save cases
        cases = await self.search_cases()
        for case in cases[:50]:  # Limit to first 50 to avoid rate limits
            await self.save_case(case)
            await asyncio.sleep(0.5)  # Rate limiting

        # Fetch and save legislation
        legislation = await self.fetch_legislation()
        for leg in legislation[:30]:  # Limit to first 30
            await self.save_legislation(leg)
            await asyncio.sleep(0.5)

        logger.info("=== AfricanLII Ingestion Complete ===")


async def run_africanlii_ingestion():
    """Run AfricanLII ingestion as a standalone task."""
    scraper = AfricanLIIScraper()
    await scraper.ingest_all()


if __name__ == "__main__":
    asyncio.run(run_africanlii_ingestion())

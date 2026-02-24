"""
Kenya Legal AI — Kenya Law Scraper
====================================
Scrapes court judgments, case law, and legal notices from kenyalaw.org.
Handles HTML parsing, PDF downloads, and metadata extraction.
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://new.kenyalaw.org"
CASE_SEARCH_URL = f"{BASE_URL}/judgments/all/"
GAZETTE_URL = f"{BASE_URL}/gazettes/"


@dataclass
class CaseMetadata:
    """Metadata for a court case."""
    case_number: str
    title: str
    court: str
    date: str
    judges: list[str]
    parties: list[str]
    citation: str
    url: str
    categories: list[str]
    source_file: Optional[str] = None


class KenyaLawScraper:
    """Scraper for kenyalaw.org case law and legal resources."""

    def __init__(self):
        settings = get_settings()
        self.raw_data_dir = Path(settings.raw_data_dir) / "kenya_law"
        self.cases_dir = self.raw_data_dir / "cases"
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.gazettes_dir = self.raw_data_dir / "gazettes"
        self.gazettes_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = Path(settings.metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _fetch_page(self, url: str) -> str:
        """Fetch a page with retry logic."""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "KenyaLegalAI-Research/1.0 "
                    "(Legal research tool; contact@example.com)"
                ),
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _download_pdf(self, url: str, save_path: Path) -> bool:
        """Download a PDF file."""
        async with httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            save_path.write_bytes(response.content)
            return True

    def _parse_case_listing(self, html: str) -> list[dict]:
        """Parse a case listing page and extract case links."""
        soup = BeautifulSoup(html, "lxml")
        cases = []

        # The new portal uses a table structure with .cell-title rows
        for row in soup.select("tr:has(td.cell-title)"):
            link_tag = row.select_one("td.cell-title a")
            date_tag = row.select_one("td.cell-date")
            
            if link_tag:
                case_url = urljoin(BASE_URL, link_tag["href"])
                title = link_tag.get_text(strip=True)
                date = date_tag.get_text(strip=True) if date_tag else ""
                
                cases.append({
                    "url": case_url,
                    "title": title,
                    "date": date
                })

        return cases

    def _parse_case_page(self, html: str, url: str) -> tuple[CaseMetadata, str]:
        """
        Parse a single case page from the new portal.
        """
        soup = BeautifulSoup(html, "lxml")

        # Extract title from h1
        title = ""
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract metadata from the definition list
        metadata_dict = {
            "Case number": "",
            "Court": "",
            "Judgment date": "",
            "Judges": [],
            "Citation": ""
        }

        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")
            if dd:
                value = dd.get_text(strip=True)
                if label in metadata_dict:
                    if label == "Judges":
                        # Split judges if they are comma separated
                        metadata_dict[label] = [j.strip() for j in value.split(",")]
                    else:
                        metadata_dict[label] = value

        # Extract judgment body text from .document-content
        judgment_text = ""
        content_div = soup.select_one(".document-content")
        if content_div:
            # Join all spans/paragraphs inside the content area
            judgment_text = content_div.get_text(separator="\n", strip=True)
        else:
            # Fallback for AKN content
            akn_body = soup.select_one(".akn-body")
            if akn_body:
                judgment_text = akn_body.get_text(separator="\n", strip=True)

        metadata = CaseMetadata(
            case_number=metadata_dict["Case number"],
            title=title or metadata_dict.get("Title", "Unknown Case"),
            court=metadata_dict["Court"],
            date=metadata_dict["Judgment date"],
            judges=metadata_dict["Judges"],
            parties=[],
            citation=metadata_dict["Citation"],
            url=url,
            categories=[],
        )

        return metadata, judgment_text

    async def scrape_case(self, case_url: str) -> Optional[dict]:
        """
        Scrape a single case page.

        Returns:
            Dictionary with case metadata and saved file paths
        """
        try:
            html = await self._fetch_page(case_url)
            metadata, judgment_text = self._parse_case_page(html, case_url)

            if not judgment_text or len(judgment_text) < 100:
                logger.warning(f"Insufficient content for case: {case_url}")
                return None

            # Create safe filename
            safe_name = re.sub(r"[^\w\-]", "_", metadata.case_number or metadata.title)
            safe_name = safe_name[:100]  # Limit filename length
            case_dir = self.cases_dir / safe_name
            case_dir.mkdir(parents=True, exist_ok=True)

            # Save judgment text
            text_path = case_dir / "judgment.txt"
            text_path.write_text(judgment_text, encoding="utf-8")

            # Save metadata
            meta_path = case_dir / "metadata.json"
            meta_path.write_text(
                json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
            )

            # Save raw HTML
            html_path = case_dir / "raw.html"
            html_path.write_text(html, encoding="utf-8")

            metadata.source_file = str(text_path)

            logger.info(f"Scraped case: {metadata.title[:60]}...")

            return {
                "metadata": asdict(metadata),
                "text_path": str(text_path),
                "meta_path": str(meta_path),
            }

        except Exception as e:
            logger.error(f"Failed to scrape {case_url}: {e}")
            return None

    async def search_cases(
        self,
        query: str = "",
        court: str = "",
        year: Optional[int] = None,
        max_pages: int = 5,
    ) -> list[dict]:
        """
        Search case law on Kenya Law.

        Args:
            query: Search query
            court: Filter by court name
            year: Filter by year
            max_pages: Maximum number of result pages to scrape

        Returns:
            List of case listing dictionaries with url and title
        """
        all_cases = []

        for page in range(1, max_pages + 1):
            params = f"?q={query}&court={court}&page={page}"
            if year:
                params += f"&year={year}"

            url = f"{CASE_SEARCH_URL}{params}"

            try:
                html = await self._fetch_page(url)
                cases = self._parse_case_listing(html)

                if not cases:
                    logger.info(f"No more results at page {page}")
                    break

                all_cases.extend(cases)
                logger.info(f"Page {page}: found {len(cases)} cases")

            except Exception as e:
                logger.error(f"Search page {page} failed: {e}")
                break

        logger.info(f"Total cases found: {len(all_cases)}")
        return all_cases

    async def scrape_gazettes(self, year: int, max_pages: int = 5) -> list[dict]:
        """Scrape Kenya Gazette notices for a specific year."""
        url = f"{GAZETTE_URL}{year}"
        logger.info(f"Scraping gazettes for year: {year}")
        
        try:
            html = await self._fetch_page(url)
            soup = BeautifulSoup(html, "lxml")
            
            notices = []
            # Gazette links have a specific pattern
            for link in soup.select('a[href*="/akn/ke/officialGazette/"]'):
                notice_url = urljoin(BASE_URL, link["href"])
                title = link.get_text(strip=True)
                
                # Check for source (PDF) link in the list or will fetch in single page
                notices.append({
                    "url": notice_url,
                    "title": title,
                    "type": "gazette"
                })
                
            logger.info(f"Found {len(notices)} gazette notices for {year}")
            return notices
            
        except Exception as e:
            logger.error(f"Failed to scrape gazettes for {year}: {e}")
            return []

    async def scrape_document_full(self, doc_info: dict) -> Optional[dict]:
        """
        Generic scraper for a document (Case or Gazette).
        Handles metadata extraction and content download.
        """
        url = doc_info["url"]
        try:
            html = await self._fetch_page(url)
            metadata, content_text = self._parse_case_page(html, url)
            
            # For Gazettes, if content_text is empty, we must download the PDF
            if not content_text or len(content_text) < 100:
                soup = BeautifulSoup(html, "lxml")
                pdf_link = soup.select_one('a.btn-primary[href$="/source"]')
                if pdf_link:
                    download_url = urljoin(BASE_URL, pdf_link["href"])
                    safe_name = re.sub(r"[^\w\-]", "_", metadata.title or "gazette")[:100]
                    save_dir = self.gazettes_dir if doc_info.get("type") == "gazette" else self.cases_dir
                    doc_dir = save_dir / safe_name
                    doc_dir.mkdir(parents=True, exist_ok=True)
                    
                    pdf_path = doc_dir / "document.pdf"
                    if await self._download_pdf(download_url, pdf_path):
                        metadata.source_file = str(pdf_path)
                        # Save metadata
                        meta_path = doc_dir / "metadata.json"
                        meta_path.write_text(json.dumps(asdict(metadata), indent=2))
                        return {"metadata": asdict(metadata), "pdf_path": str(pdf_path)}

            # Usual text path
            return await self.scrape_case(url)

        except Exception as e:
            logger.error(f"Failed to scrape document {url}: {e}")
            return None


async def run_case_scraping(
    court: str = "",
    year: Optional[int] = None,
    max_pages: int = 3,
):
    """Run case law scraping from Kenya Law."""
    scraper = KenyaLawScraper()

    logger.info("Starting Kenya Law case scraping...")

    # Search for cases
    cases = await scraper.search_cases(
        court=court, year=year, max_pages=max_pages
    )

    # Scrape each case
    results = []
    for case_info in cases:
        result = await scraper.scrape_case(case_info["url"])
        if result:
            results.append(result)

    # Save results index
    index_path = scraper.metadata_dir / "scraped_cases_index.json"
    index_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    logger.info(
        f"Scraping complete. Successfully scraped {len(results)}/{len(cases)} cases."
    )
    return results


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    # Scrape 1 page of 2024 results for testing
    asyncio.run(run_case_scraping(year=2024, max_pages=1))

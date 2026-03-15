"""
Kenya Legal AI — Elections Scraper
=====================================
Scrapes Election Petitions, rulings, and electoral materials from kenyalaw.org.

Coverage:
  - Election Petitions 2022 (Presidential, Governor, Senator, Women Rep, MNA, MCA, Party List)
  - Election Petitions 2017 (August + November Presidential, Governor, Senator, etc.)
  - Election Petitions 2013 (JCE Reports, Presidential Petition Summary)
  - Election Petition Rules 2017
  - Electoral Laws Grey Book
  - Electoral Process in Kenya
  - 2017 Political Parties Disputes Tribunal
  - 2017 Party Primaries Decisions

Saves to: data/raw/kenya_law/elections/{year}/{election_type}/
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "http://kenyalaw.org"

# Sitemap-mapped sections for electoral content
ELECTION_SECTIONS = [
    # 2022 election petitions
    {
        "year": "2022", "election_type": "presidential",
        "label": "2022 Presidential Petition",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-presidential-2022",
    },
    {
        "year": "2022", "election_type": "governor",
        "label": "Governor Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-governor-2022",
    },
    {
        "year": "2022", "election_type": "senator",
        "label": "Senator Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-senator-2022",
    },
    {
        "year": "2022", "election_type": "women_reps",
        "label": "Women Representatives Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-women-reps-2022",
    },
    {
        "year": "2022", "election_type": "mna",
        "label": "Members of National Assembly Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-mna-2022",
    },
    {
        "year": "2022", "election_type": "mca",
        "label": "Members of County Assembly Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-mca-2022",
    },
    {
        "year": "2022", "election_type": "party_list",
        "label": "Party List Petitions 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-party-list-2022",
    },
    # 2017 election petitions
    {
        "year": "2017", "election_type": "presidential_nov",
        "label": "November 2017 Presidential Election Petition",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-presidential-nov-2017",
    },
    {
        "year": "2017", "election_type": "presidential_aug",
        "label": "August 2017 Presidential Election Petition",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-presidential-aug-2017",
    },
    {
        "year": "2017", "election_type": "governor",
        "label": "Governor Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-governor-2017",
    },
    {
        "year": "2017", "election_type": "senator",
        "label": "Senator Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-senator-2017",
    },
    {
        "year": "2017", "election_type": "women_reps",
        "label": "Women Representatives Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-women-reps-2017",
    },
    {
        "year": "2017", "election_type": "mna",
        "label": "Members of National Assembly Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-mna-2017",
    },
    {
        "year": "2017", "election_type": "mca",
        "label": "Members of County Assembly Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-mca-2017",
    },
    {
        "year": "2017", "election_type": "party_list",
        "label": "Party List Petitions 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-party-list-2017",
    },
    {
        "year": "2017", "election_type": "ppdt",
        "label": "2017 Political Parties Disputes Tribunal",
        "url": "http://kenyalaw.org/kl/index.php?id=ppdt-2017",
    },
    {
        "year": "2017", "election_type": "party_primaries",
        "label": "2017 Party Primaries Decisions",
        "url": "http://kenyalaw.org/kl/index.php?id=party-primaries-2017",
    },
    {
        "year": "2017", "election_type": "petition_rules",
        "label": "Election Petition Rules 2017",
        "url": "http://kenyalaw.org/kl/index.php?id=election-petition-rules-2017",
    },
    # 2013 election petitions
    {
        "year": "2013", "election_type": "all",
        "label": "Election Petitions 2013",
        "url": "http://kenyalaw.org/kl/index.php?id=elections-2013",
    },
    {
        "year": "2013", "election_type": "jce_reports",
        "label": "Judiciary Committee on Election (JCE) Reports",
        "url": "http://kenyalaw.org/kl/index.php?id=jce-reports-2013",
    },
    {
        "year": "2013", "election_type": "presidential_summary",
        "label": "Presidential Petition Mwananchi Friendly Version",
        "url": "http://kenyalaw.org/kl/index.php?id=presidential-petition-2013-summary",
    },
    # Cross-election resources
    {
        "year": "general", "election_type": "electoral_laws",
        "label": "Electoral Laws Grey Book",
        "url": "http://kenyalaw.org/kl/index.php?id=electoral-laws-grey-book",
    },
    {
        "year": "general", "election_type": "electoral_process",
        "label": "Electoral Process in Kenya",
        "url": "http://kenyalaw.org/kl/index.php?id=electoral-process-kenya",
    },
    {
        "year": "general", "election_type": "election_preparedness",
        "label": "Election Preparedness 2022",
        "url": "http://kenyalaw.org/kl/index.php?id=election-preparedness-2022",
    },
]


@dataclass
class ElectionPetition:
    """Metadata for an election petition or electoral document."""
    year: str
    election_type: str
    label: str
    title: str
    court: str
    url: str
    source_file: Optional[str] = None


class ElectionsScraper:
    """Scraper for Kenya election petitions and electoral documents."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "elections"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "elections_checkpoint.json"
        self.checkpoint = self._load_checkpoint()
        self.semaphore = asyncio.Semaphore(2)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            try:
                return json.loads(self.checkpoint_path.read_text())
            except Exception:
                pass
        return {"completed": [], "total": 0}

    def _save_checkpoint(self):
        self.checkpoint_path.write_text(json.dumps(self.checkpoint, indent=2))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=15))
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(
            timeout=30, headers=self.headers, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _parse_petition_links(self, html: str) -> List[dict]:
        """Extract individual petition/document links from a section page."""
        soup = BeautifulSoup(html, "lxml")
        docs = []

        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 5:
                continue
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue

            # Extract court name if present
            court_m = re.search(
                r"(Supreme Court|High Court|Court of Appeal|Magistrate)", text, re.I
            )
            court = court_m.group(0) if court_m else ""

            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            docs.append({"title": text, "url": full_url, "court": court})

        return docs

    async def scrape_document(self, doc_info: dict, section: dict) -> Optional[dict]:
        """Scrape a single election petition or document."""
        async with self.semaphore:
            url = doc_info["url"]
            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title_tag = soup.find("h1") or soup.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else doc_info["title"]

                content_div = soup.select_one(".document-content, .akn-body, #content")
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = ElectionPetition(
                    year=section["year"],
                    election_type=section["election_type"],
                    label=section["label"],
                    title=title,
                    court=doc_info.get("court", ""),
                    url=url,
                )

                safe_title = re.sub(r"[^\w\-]", "_", title)[:80]
                doc_dir = (
                    self.output_dir
                    / section["year"]
                    / section["election_type"]
                    / safe_title
                )
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="/source"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "petition.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF failed {pdf_url}: {e}")

                meta_path = doc_dir / "metadata.json"
                meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
                logger.info(f"Scraped election doc: {title[:60]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed {url}: {e}")
                return None

    async def scrape_section(self, section: dict, limit: Optional[int] = None) -> int:
        """Scrape all documents in a given election section."""
        key = f"{section['year']}_{section['election_type']}"
        if key in self.checkpoint.get("completed", []):
            logger.info(f"Skipping {key}")
            return 0

        try:
            html = await self._fetch(section["url"])
            docs = self._parse_petition_links(html)
            if not docs:
                # The page itself might be the document
                docs = [{"title": section["label"], "url": section["url"], "court": ""}]
            if limit:
                docs = docs[:limit]

            logger.info(f"{section['label']}: {len(docs)} documents")
            count = 0
            for doc in docs:
                result = await self.scrape_document(doc, section)
                if result:
                    count += 1
                await asyncio.sleep(2)

            self.checkpoint.setdefault("completed", []).append(key)
            self.checkpoint["total"] = self.checkpoint.get("total", 0) + count
            self._save_checkpoint()
            return count

        except Exception as e:
            logger.error(f"Error scraping section {key}: {e}")
            return 0

    async def run_bulk_ingestion(self, limit_per_section: Optional[int] = None):
        """Scrape all election sections."""
        for section in ELECTION_SECTIONS:
            await self.scrape_section(section, limit=limit_per_section)
            await asyncio.sleep(3)
        logger.info(f"Elections ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_elections_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = ElectionsScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Elections ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_elections_ingestion())

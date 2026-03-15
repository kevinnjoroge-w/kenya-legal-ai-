"""
Kenya Legal AI — Repealed Statutes Scraper
===========================================
Scrapes all Repealed Statutes from kenyalaw.org.
These are laws that were once in force but have been repealed/superseded.
Historical context is essential for understanding legal evolution since independence.

Saves to: data/raw/kenya_law/repealed_statutes/
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
REPEALED_STATUTES_INDEX = "http://kenyalaw.org/kl/index.php?id=repealed-statutes"


@dataclass
class RepealedStatute:
    """Metadata for a repealed statute."""
    title: str
    number: str
    year_enacted: str
    year_repealed: str
    repealing_act: str
    url: str
    source_file: Optional[str] = None


class RepealedStatutesScraper:
    """Scraper for Kenya's Repealed Statutes database."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "repealed_statutes"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "repealed_statutes_checkpoint.json"
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
        return {"visited": [], "total": 0}

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

    def _parse_statute_links(self, html: str) -> List[dict]:
        """Parse the repealed statutes index for individual statute links."""
        soup = BeautifulSoup(html, "lxml")
        statutes = []

        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 8:
                continue
            if "index.php?id=" not in href and not href.endswith(".pdf"):
                continue
            if any(nav in text.lower() for nav in ["home", "search", "back", "index"]):
                continue

            # Extract Act number if present
            num_m = re.search(r"(?:Cap\.?\s*(\d+[A-Z]?)|No\.?\s*(\d+)\s+of\s+(\d{4}))", text, re.I)

            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            if full_url not in [s["url"] for s in statutes]:
                statutes.append({
                    "title": text,
                    "url": full_url,
                    "number": num_m.group(0) if num_m else "",
                })

        return statutes

    def _parse_statute_page(self, html: str, url: str) -> tuple:
        """Extract metadata and text from a single repealed statute page."""
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("h1") or soup.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Act"

        # Metadata from definition lists or tables
        year_enacted = ""
        year_repealed = ""
        repealing_act = ""
        number = ""

        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            val = dd.get_text(strip=True) if dd else ""
            if "enact" in label or "commenc" in label:
                year_m = re.search(r"\d{4}", val)
                year_enacted = year_m.group() if year_m else val
            elif "repeal" in label:
                year_m = re.search(r"\d{4}", val)
                year_repealed = year_m.group() if year_m else val
                repealing_act = val
            elif "number" in label or "cap" in label:
                number = val

        # Also scan tables
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                if "enacted" in label and not year_enacted:
                    year_enacted = re.search(r"\d{4}", val).group() if re.search(r"\d{4}", val) else val
                elif "repealed" in label and not year_repealed:
                    year_repealed = re.search(r"\d{4}", val).group() if re.search(r"\d{4}", val) else val
                    if not repealing_act:
                        repealing_act = val

        content_div = soup.select_one(".document-content, .akn-body, #content")
        text = content_div.get_text(separator="\n", strip=True) if content_div else ""

        metadata = RepealedStatute(
            title=title,
            number=number,
            year_enacted=year_enacted,
            year_repealed=year_repealed,
            repealing_act=repealing_act,
            url=url,
        )
        return metadata, text

    async def scrape_statute(self, statute_info: dict) -> Optional[dict]:
        """Scrape a single repealed statute."""
        async with self.semaphore:
            url = statute_info["url"]
            if url in self.checkpoint.get("visited", []):
                return None

            try:
                html = await self._fetch(url)
                metadata, text = self._parse_statute_page(html, url)

                safe_title = re.sub(r"[^\w\-]", "_", metadata.title)[:100]
                doc_dir = self.output_dir / safe_title
                doc_dir.mkdir(parents=True, exist_ok=True)

                if text and len(text) > 100:
                    txt_path = doc_dir / "content.txt"
                    txt_path.write_text(text, encoding="utf-8")
                    metadata.source_file = str(txt_path)
                else:
                    soup = BeautifulSoup(html, "lxml")
                    pdf_link = soup.select_one('a[href$=".pdf"], a[href*="/source"]')
                    if pdf_link:
                        pdf_url = urljoin(BASE_URL, pdf_link["href"])
                        try:
                            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                                r = await client.get(pdf_url)
                                r.raise_for_status()
                                pdf_path = doc_dir / "statute.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF failed {pdf_url}: {e}")

                (doc_dir / "metadata.json").write_text(
                    json.dumps(asdict(metadata), indent=2, ensure_ascii=False)
                )
                self.checkpoint.setdefault("visited", []).append(url)
                self.checkpoint["total"] = self.checkpoint.get("total", 0) + 1
                self._save_checkpoint()
                logger.info(f"Scraped repealed statute: {metadata.title[:60]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed statute {url}: {e}")
                return None

    async def run_bulk_ingestion(self, limit: Optional[int] = None):
        """Scrape all repealed statutes."""
        html = await self._fetch(REPEALED_STATUTES_INDEX)
        statutes = self._parse_statute_links(html)
        if limit:
            statutes = statutes[:limit]

        logger.info(f"Repealed Statutes: {len(statutes)} found")
        for statute in statutes:
            await self.scrape_statute(statute)
            await asyncio.sleep(2)

        logger.info(f"Repealed Statutes ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_repealed_statutes_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = RepealedStatutesScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Repealed Statutes ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_repealed_statutes_ingestion())

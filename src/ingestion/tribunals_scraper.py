"""
Kenya Legal AI — Tribunals Scraper
====================================
Scrapes decisions from all 15 tribunals listed on kenyalaw.org.

Tribunals covered:
  Business Premises Rent, Competition, Cooperative, Education Appeals,
  HIV & AIDS, Industrial Property, Legal Education Appeals, MSET,
  National Civil Aviation, NET, PPDT, Standard, Sports Dispute,
  Tax Appeals, Transport Licensing Appeals Board

Saves to: data/raw/kenya_law/tribunals/{tribunal_slug}/{year}/
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

# All 15 tribunals from the sitemap with their known slug names
TRIBUNALS = [
    {
        "name": "Business Premises Rent Tribunal",
        "slug": "business_premises_rent",
        "url": "http://kenyalaw.org/kl/index.php?id=business-premises-rent-tribunal",
    },
    {
        "name": "Competition Tribunal",
        "slug": "competition",
        "url": "http://kenyalaw.org/kl/index.php?id=competition-tribunal",
    },
    {
        "name": "Cooperative Tribunal",
        "slug": "cooperative",
        "url": "http://kenyalaw.org/kl/index.php?id=cooperative-tribunal",
    },
    {
        "name": "Education Appeals Tribunal",
        "slug": "education_appeals",
        "url": "http://kenyalaw.org/kl/index.php?id=education-appeals-tribunal",
    },
    {
        "name": "HIV and AIDS Tribunal",
        "slug": "hiv_aids",
        "url": "http://kenyalaw.org/kl/index.php?id=hiv-and-aids-tribunal",
    },
    {
        "name": "Industrial Property Tribunal",
        "slug": "industrial_property",
        "url": "http://kenyalaw.org/kl/index.php?id=industrial-property-tribunal",
    },
    {
        "name": "Legal Education Appeals Tribunal",
        "slug": "legal_education_appeals",
        "url": "http://kenyalaw.org/kl/index.php?id=legal-education-appeals-tribunal",
    },
    {
        "name": "Micro and Small Enterprises Tribunal",
        "slug": "mset",
        "url": "http://kenyalaw.org/kl/index.php?id=micro-small-enterprises-tribunal",
    },
    {
        "name": "National Civil Aviation Administrative Review Tribunal",
        "slug": "civil_aviation",
        "url": "http://kenyalaw.org/kl/index.php?id=national-civil-aviation-tribunal",
    },
    {
        "name": "National Environment Tribunal",
        "slug": "net",
        "url": "http://kenyalaw.org/kl/index.php?id=national-environment-tribunal",
    },
    {
        "name": "Political Parties Disputes Tribunal",
        "slug": "ppdt",
        "url": "http://kenyalaw.org/kl/index.php?id=political-parties-disputes-tribunal",
    },
    {
        "name": "Standard Tribunal",
        "slug": "standard",
        "url": "http://kenyalaw.org/kl/index.php?id=standard-tribunal",
    },
    {
        "name": "Sports Dispute Tribunal",
        "slug": "sports_dispute",
        "url": "http://kenyalaw.org/kl/index.php?id=sports-dispute-tribunal",
    },
    {
        "name": "Tax Appeals Tribunal",
        "slug": "tax_appeals",
        "url": "http://kenyalaw.org/kl/index.php?id=tax-appeals-tribunal",
    },
    {
        "name": "Transport Licensing Appeals Board",
        "slug": "transport_licensing",
        "url": "http://kenyalaw.org/kl/index.php?id=transport-licensing-appeals-board",
    },
]


@dataclass
class TribunalDecision:
    """Metadata for a tribunal decision."""
    tribunal_name: str
    tribunal_slug: str
    title: str
    case_number: str
    date: str
    url: str
    source_file: Optional[str] = None


class TribunalsScraper:
    """Scraper for all Kenyan tribunal decisions from kenyalaw.org."""

    def __init__(self):
        settings = get_settings()
        self.output_dir = Path(settings.raw_data_dir) / "kenya_law" / "tribunals"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = Path(settings.metadata_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.meta_dir / "tribunals_checkpoint.json"
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

    def _parse_decision_links(self, html: str) -> List[dict]:
        """Parse a tribunal index page for decision links."""
        soup = BeautifulSoup(html, "lxml")
        decisions = []

        # Try table rows with links (common pattern on kenyalaw.org/kl)
        for tr in soup.find_all("tr"):
            a = tr.find("a", href=True)
            if not a:
                continue
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or "index.php" not in href:
                continue

            # Try to extract date from row cells
            cells = tr.find_all("td")
            date = cells[-1].get_text(strip=True) if len(cells) > 1 else ""
            case_num_match = re.search(r"(?:Case|Cause|Ref)\.?\s*No\.?\s*([\w/\-]+)", text, re.I)

            decisions.append({
                "title": text,
                "url": urljoin(BASE_URL, href),
                "date": date,
                "case_number": case_num_match.group(0) if case_num_match else "",
            })

        # Also check generic link lists
        if not decisions:
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if not text or len(text) < 5:
                    continue
                if "index.php?id=" in href and href != soup.find("base", href=True):
                    date_m = re.search(r"\d{4}", text)
                    decisions.append({
                        "title": text,
                        "url": urljoin(BASE_URL, href),
                        "date": date_m.group() if date_m else "",
                        "case_number": "",
                    })

        return decisions

    async def scrape_decision(
        self, decision_info: dict, tribunal: dict
    ) -> Optional[dict]:
        """Scrape a single tribunal decision."""
        async with self.semaphore:
            url = decision_info["url"]
            try:
                html = await self._fetch(url)
                soup = BeautifulSoup(html, "lxml")

                title_tag = soup.find("h1") or soup.find("h2")
                title = title_tag.get_text(strip=True) if title_tag else decision_info["title"]

                date_m = re.search(
                    r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
                    html,
                )
                date = date_m.group() if date_m else decision_info.get("date", "")
                year = re.search(r"\d{4}", date).group() if re.search(r"\d{4}", date) else "unknown"

                content_div = soup.select_one(".document-content, .akn-body, #content")
                text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                metadata = TribunalDecision(
                    tribunal_name=tribunal["name"],
                    tribunal_slug=tribunal["slug"],
                    title=title,
                    case_number=decision_info.get("case_number", ""),
                    date=date,
                    url=url,
                )

                safe_title = re.sub(r"[^\w\-]", "_", title)[:80]
                doc_dir = self.output_dir / tribunal["slug"] / year / safe_title
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
                                pdf_path = doc_dir / "decision.pdf"
                                pdf_path.write_bytes(r.content)
                                metadata.source_file = str(pdf_path)
                        except Exception as e:
                            logger.warning(f"PDF download failed {pdf_url}: {e}")

                meta_path = doc_dir / "metadata.json"
                meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
                logger.info(f"Scraped: [{tribunal['slug']}] {title[:50]}")
                return {"metadata": asdict(metadata), "path": str(doc_dir)}

            except Exception as e:
                logger.error(f"Failed decision {url}: {e}")
                return None

    async def scrape_tribunal(self, tribunal: dict, limit: Optional[int] = None) -> int:
        """Scrape all decisions for one tribunal."""
        slug = tribunal["slug"]
        if slug in self.checkpoint.get("completed", []):
            logger.info(f"Skipping tribunal {slug} (already done)")
            return 0

        try:
            html = await self._fetch(tribunal["url"])
            decisions = self._parse_decision_links(html)
            if limit:
                decisions = decisions[:limit]
            logger.info(f"{tribunal['name']}: found {len(decisions)} decisions")

            count = 0
            for dec in decisions:
                result = await self.scrape_decision(dec, tribunal)
                if result:
                    count += 1
                await asyncio.sleep(2)

            self.checkpoint.setdefault("completed", []).append(slug)
            self.checkpoint["total"] = self.checkpoint.get("total", 0) + count
            self._save_checkpoint()
            logger.info(f"  Done: {count}/{len(decisions)} decisions for {slug}")
            return count

        except Exception as e:
            logger.error(f"Error scraping tribunal {slug}: {e}")
            return 0

    async def run_bulk_ingestion(self, limit_per_tribunal: Optional[int] = None):
        """Scrape all 15 tribunals."""
        for tribunal in TRIBUNALS:
            await self.scrape_tribunal(tribunal, limit=limit_per_tribunal)
            await asyncio.sleep(4)

        logger.info(f"Tribunals ingestion complete. Total: {self.checkpoint.get('total', 0)}")


async def run_tribunals_ingestion():
    """Entry point for mass_ingest.py."""
    scraper = TribunalsScraper()
    await scraper.run_bulk_ingestion()
    logger.info("Tribunals ingestion finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_tribunals_ingestion())

"""
Kenya Legal AI — Deduplication Tracker
=======================================
Tracks downloaded documents by URL/filename to prevent re-downloading.
Uses JSON-based persistent registry.

Registry structure:
{
    "downloaded_urls": {
        "https://example.com/doc.pdf": {
            "timestamp": "2026-05-25T01:14:57",
            "local_path": "data/raw/kenya_law/doc.pdf",
            "file_hash": "abc123...",
            "format": "pdf"
        }
    }
}
"""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Set
from urllib.parse import urlparse

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class DeduplicationTracker:
    """Tracks downloaded documents to prevent duplicates."""

    def __init__(self, registry_file: Optional[Path] = None):
        """
        Initialize deduplication tracker.

        Args:
            registry_file: Path to JSON registry file. If None, uses default from settings.
        """
        if registry_file is None:
            settings = get_settings()
            metadata_dir = Path(settings.metadata_dir)
            registry_file = metadata_dir / "dedup_registry.json"

        self.registry_file = Path(registry_file)
        self.registry: Dict = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load deduplication registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load dedup registry: {e}. Starting fresh.")
                return {"downloaded_urls": {}, "downloaded_files": {}}

        return {"downloaded_urls": {}, "downloaded_files": {}}

    def _save_registry(self) -> None:
        """Save deduplication registry to file."""
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save dedup registry: {e}")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for comparison (removes fragments, trailing slashes, etc)."""
        # Remove fragments
        url = url.split('#')[0]
        # Remove query params (optional - comment out if you want to track those separately)
        # url = url.split('?')[0]
        # Remove trailing slashes
        url = url.rstrip('/')
        return url.lower()

    @staticmethod
    def _calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def is_url_downloaded(self, url: str) -> bool:
        """
        Check if a URL has already been downloaded.

        Args:
            url: The URL to check

        Returns:
            True if URL has been downloaded, False otherwise
        """
        normalized_url = self._normalize_url(url)
        return normalized_url in self.registry.get("downloaded_urls", {})

    def is_file_downloaded(self, file_path: Path) -> bool:
        """
        Check if a file (by hash) has already been downloaded.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file with same content has been downloaded, False otherwise
        """
        if not file_path.exists():
            return False

        file_hash = self._calculate_file_hash(file_path)
        return file_hash in self.registry.get("downloaded_files", {})

    def mark_downloaded(
        self,
        url: str,
        local_path: Path,
        doc_format: str = "unknown"
    ) -> None:
        """
        Mark a URL as downloaded.

        Args:
            url: The source URL
            local_path: Path where file was saved locally
            doc_format: File format (pdf, docx, html, xml, txt)
        """
        normalized_url = self._normalize_url(url)
        file_hash = self._calculate_file_hash(Path(local_path)) if Path(local_path).exists() else ""

        self.registry["downloaded_urls"][normalized_url] = {
            "timestamp": datetime.now().isoformat(),
            "local_path": str(local_path),
            "file_hash": file_hash,
            "format": doc_format
        }

        if file_hash:
            self.registry["downloaded_files"][file_hash] = {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "local_path": str(local_path),
                "format": doc_format
            }

        self._save_registry()
        logger.info(f"Marked as downloaded: {normalized_url}")

    def get_download_info(self, url: str) -> Optional[Dict]:
        """
        Get download information for a URL.

        Args:
            url: The URL to look up

        Returns:
            Dictionary with download info or None if not found
        """
        normalized_url = self._normalize_url(url)
        return self.registry.get("downloaded_urls", {}).get(normalized_url)

    def get_downloaded_urls(self, source: Optional[str] = None) -> Set[str]:
        """
        Get all downloaded URLs, optionally filtered by source.

        Args:
            source: Optional source to filter by (e.g., 'kenya_law', 'judiciary')

        Returns:
            Set of downloaded URLs
        """
        urls = set(self.registry.get("downloaded_urls", {}).keys())

        if source:
            # Filter by URL pattern containing source
            urls = {url for url in urls if source.lower() in url.lower()}

        return urls

    def get_statistics(self) -> Dict:
        """Get deduplication statistics."""
        return {
            "total_unique_urls": len(self.registry.get("downloaded_urls", {})),
            "total_unique_files": len(self.registry.get("downloaded_files", {})),
            "urls_by_format": self._count_by_format("downloaded_urls"),
            "registry_file": str(self.registry_file)
        }

    def _count_by_format(self, registry_key: str) -> Dict[str, int]:
        """Count entries by file format."""
        counts = {}
        for entry in self.registry.get(registry_key, {}).values():
            fmt = entry.get("format", "unknown")
            counts[fmt] = counts.get(fmt, 0) + 1
        return counts

    def reset_registry(self, confirm: bool = False) -> bool:
        """
        Reset the entire deduplication registry.

        Args:
            confirm: Must be True to actually reset (safety measure)

        Returns:
            True if reset, False otherwise
        """
        if not confirm:
            logger.warning("Reset not confirmed. Pass confirm=True to actually reset.")
            return False

        self.registry = {"downloaded_urls": {}, "downloaded_files": {}}
        self._save_registry()
        logger.warning("Deduplication registry has been reset!")
        return True

    def remove_url(self, url: str) -> bool:
        """
        Remove a URL from the registry.

        Args:
            url: URL to remove

        Returns:
            True if removed, False if not found
        """
        normalized_url = self._normalize_url(url)

        if normalized_url in self.registry.get("downloaded_urls", {}):
            del self.registry["downloaded_urls"][normalized_url]
            self._save_registry()
            logger.info(f"Removed from registry: {normalized_url}")
            return True

        return False

    def get_duplicate_urls(self, url: str, tolerance: float = 0.9) -> Set[str]:
        """
        Find URLs similar to the given URL (potential duplicates).

        Uses simple string similarity heuristic.

        Args:
            url: URL to find duplicates for
            tolerance: Similarity threshold (0-1)

        Returns:
            Set of similar URLs in registry
        """
        normalized = self._normalize_url(url).lower()
        similar = set()

        for registered_url in self.registry.get("downloaded_urls", {}).keys():
            if self._string_similarity(normalized, registered_url) >= tolerance:
                similar.add(registered_url)

        return similar

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> float:
        """Simple string similarity using character overlap."""
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if longer == s1 else s1

        if len(longer) == 0:
            return 1.0

        match_distance = len(longer) - len(shorter)
        matches = sum(1 for i, c in enumerate(shorter) if c == longer[i])

        return matches / len(longer)


def get_dedup_tracker(registry_file: Optional[Path] = None) -> DeduplicationTracker:
    """Get a deduplication tracker instance."""
    return DeduplicationTracker(registry_file)

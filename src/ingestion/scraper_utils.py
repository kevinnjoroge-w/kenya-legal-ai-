"""
Kenya Legal AI — Scraper Utilities
===================================
Utility functions for scrapers to leverage deduplication and multi-format support.
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Any

from src.ingestion.deduplication_tracker import DeduplicationTracker
from src.ingestion.document_handler import extract_text_from_file

logger = logging.getLogger(__name__)


class DedupAwareScraper:
    """Mixin class for scrapers to integrate deduplication tracking."""

    def __init__(self):
        """Initialize with dedup tracker."""
        self.dedup_tracker = None

    def init_dedup_tracker(self) -> DeduplicationTracker:
        """Initialize or get the deduplication tracker."""
        if self.dedup_tracker is None:
            from src.ingestion.deduplication_tracker import get_dedup_tracker
            self.dedup_tracker = get_dedup_tracker()
        return self.dedup_tracker

    def should_download(self, url: str) -> bool:
        """
        Check if a URL should be downloaded (not already in registry).

        Args:
            url: URL to check

        Returns:
            True if should download, False if already downloaded
        """
        tracker = self.init_dedup_tracker()
        is_downloaded = tracker.is_url_downloaded(url)

        if is_downloaded:
            logger.debug(f"URL already downloaded, skipping: {url}")
            info = tracker.get_download_info(url)
            logger.debug(f"  Previously saved to: {info.get('local_path')}")

        return not is_downloaded

    def mark_downloaded(
        self,
        url: str,
        local_path: Path,
        doc_format: str = "unknown"
    ) -> None:
        """
        Mark a URL as downloaded in the dedup registry.

        Args:
            url: Source URL
            local_path: Path where file was saved
            doc_format: File format (pdf, docx, html, etc)
        """
        tracker = self.init_dedup_tracker()
        tracker.mark_downloaded(url, local_path, doc_format)

    def download_with_dedup(
        self,
        url: str,
        download_func: Callable,
        save_path: Path,
        doc_format: str = "unknown",
        **kwargs
    ) -> Optional[Path]:
        """
        Download a file with automatic deduplication check.

        Args:
            url: URL to download
            download_func: Function to call for download (receives url, save_path, **kwargs)
            save_path: Where to save the file
            doc_format: File format
            **kwargs: Additional arguments to pass to download_func

        Returns:
            Path to downloaded file or None if skipped/failed
        """
        # Check if already downloaded
        if not self.should_download(url):
            return None

        # Download
        try:
            logger.info(f"Downloading: {url}")
            result_path = download_func(url, save_path, **kwargs)

            if result_path:
                # Mark as downloaded
                self.mark_downloaded(url, Path(result_path), doc_format)
                logger.info(f"Marked as downloaded: {url}")
                return result_path

            logger.warning(f"Download returned no path: {url}")
            return None

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None

    def get_dedup_stats(self) -> dict:
        """Get deduplication statistics."""
        tracker = self.init_dedup_tracker()
        return tracker.get_statistics()


def extract_and_chunk_multi_format(
    file_path: Path,
    processor,  # LegalDocumentProcessor instance
    document_type: str = "legal_notice",
    source: str = "generic",
    metadata: Optional[dict] = None
) -> list:
    """
    Extract text from any format and chunk it for embedding.

    Args:
        file_path: Path to document
        processor: LegalDocumentProcessor instance
        document_type: Type of document
        source: Data source name
        metadata: Additional metadata

    Returns:
        List of DocumentChunk objects
    """
    return processor.process_multi_format_document(
        file_path=file_path,
        document_type=document_type,
        source=source,
        metadata=metadata
    )


def bulk_download_with_dedup(
    urls: list,
    download_func: Callable,
    save_dir: Path,
    doc_format: str = "unknown",
    stop_on_error: bool = False
) -> dict:
    """
    Bulk download multiple URLs with deduplication.

    Args:
        urls: List of URLs to download
        download_func: Function that downloads (receives url, save_path)
        save_dir: Directory to save files
        doc_format: File format
        stop_on_error: Stop on first error

    Returns:
        Dictionary with stats: {'success': n, 'skipped': n, 'failed': n, 'paths': []}
    """
    from src.ingestion.deduplication_tracker import get_dedup_tracker

    tracker = get_dedup_tracker()
    stats = {
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'paths': []
    }

    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    for url in urls:
        # Check if already downloaded
        if tracker.is_url_downloaded(url):
            logger.debug(f"Skipping already downloaded: {url}")
            stats['skipped'] += 1
            continue

        # Generate save path
        filename = url.split('/')[-1].split('?')[0]
        if not filename or len(filename) < 3:
            filename = f"document_{len(stats['paths'])}{Path(url).suffix}"

        save_path = save_dir / filename

        # Download
        try:
            logger.info(f"Downloading: {url}")
            result = download_func(url, save_path)

            if result:
                tracker.mark_downloaded(url, save_path, doc_format)
                stats['success'] += 1
                stats['paths'].append(str(result))
                logger.info(f"Downloaded successfully: {url}")
            else:
                stats['failed'] += 1
                logger.warning(f"Download failed: {url}")

                if stop_on_error:
                    break

        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            stats['failed'] += 1

            if stop_on_error:
                break

    logger.info(
        f"Bulk download complete: "
        f"success={stats['success']}, "
        f"skipped={stats['skipped']}, "
        f"failed={stats['failed']}"
    )

    return stats

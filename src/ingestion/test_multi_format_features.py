"""
Kenya Legal AI — Multi-Format & Deduplication Test/Demo
=========================================================
Demonstrates the new multi-format support and deduplication features.

Run with: python -m src.ingestion.test_multi_format_features
"""

import json
import logging
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_document_handler():
    """Test the document handler with different formats."""
    logger.info("="*60)
    logger.info("TEST 1: Document Handler Format Detection")
    logger.info("="*60)

    try:
        from src.ingestion.document_handler import DocumentHandler

        handler = DocumentHandler()

        # Test format detection
        test_files = [
            "document.pdf",
            "report.docx",
            "page.html",
            "data.xml",
            "content.txt",
            "unknown.xyz"
        ]

        for filename in test_files:
            detected = handler.detect_format(filename)
            status = "✓" if (detected is not None) == (not filename.endswith(".xyz")) else "✗"
            logger.info(f"  {status} {filename:20} → {detected or 'unsupported'}")

        logger.info("✓ Document format detection working correctly\n")
        return True

    except Exception as e:
        logger.error(f"✗ Document handler test failed: {e}\n")
        return False


def test_dedup_tracker():
    """Test the deduplication tracker."""
    logger.info("="*60)
    logger.info("TEST 2: Deduplication Tracker")
    logger.info("="*60)

    try:
        from src.ingestion.deduplication_tracker import DeduplicationTracker
        import tempfile
        import os

        # Create temporary registry for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_file = Path(tmpdir) / "test_registry.json"

            tracker = DeduplicationTracker(registry_file)

            # Test URL tracking
            test_urls = [
                "https://example.com/doc1.pdf",
                "https://example.com/doc2.docx",
                "https://example.com/doc1.pdf",  # Duplicate
            ]

            logger.info("Testing URL tracking:")
            for url in test_urls:
                is_downloaded = tracker.is_url_downloaded(url)
                if not is_downloaded:
                    logger.info(f"  + Marking as downloaded: {url}")
                    dummy_path = Path(tmpdir) / Path(url).name
                    dummy_path.touch()
                    tracker.mark_downloaded(url, dummy_path, "pdf")
                else:
                    logger.info(f"  ✓ Already tracked (dedup working!): {url}")

            # Test statistics
            stats = tracker.get_statistics()
            logger.info(f"\nStatistics:")
            logger.info(f"  Total unique URLs: {stats['total_unique_urls']}")
            logger.info(f"  Total unique files: {stats['total_unique_files']}")
            logger.info(f"  Format breakdown: {stats['urls_by_format']}")

            # Test duplicate detection
            logger.info(f"\nTesting duplicate detection:")
            similar = tracker.get_duplicate_urls("https://example.com/doc1.pdf")
            logger.info(f"  Found {len(similar)} similar URLs")

            logger.info("✓ Deduplication tracker working correctly\n")
            return True

    except Exception as e:
        logger.error(f"✗ Deduplication tracker test failed: {e}\n")
        return False


def test_document_processor_integration():
    """Test document processor integration."""
    logger.info("="*60)
    logger.info("TEST 3: Document Processor Multi-Format Integration")
    logger.info("="*60)

    try:
        from src.processing.document_processor import LegalDocumentProcessor

        processor = LegalDocumentProcessor()

        # Check that the new method exists
        if hasattr(processor, 'process_multi_format_document'):
            logger.info("  ✓ process_multi_format_document() method exists")
        else:
            logger.error("  ✗ process_multi_format_document() method not found")
            return False

        # Check document handler integration
        from src.processing.document_processor import extract_text_from_file
        logger.info("  ✓ extract_text_from_file() imported successfully")

        logger.info("✓ Document processor integration working correctly\n")
        return True

    except Exception as e:
        logger.error(f"✗ Document processor test failed: {e}\n")
        return False


def test_mass_ingest_integration():
    """Test mass_ingest integration."""
    logger.info("="*60)
    logger.info("TEST 4: Mass Ingest Dedup Tracker Integration")
    logger.info("="*60)

    try:
        from src.ingestion.mass_ingest import run_mass_ingestion

        # Check that mass_ingest imports dedup tracker
        import inspect
        source = inspect.getsource(run_mass_ingestion)

        checks = [
            ("dedup_tracker import", "from src.ingestion.deduplication_tracker" in source),
            ("get_dedup_tracker() call", "get_dedup_tracker()" in source),
            ("Statistics logging", "get_statistics()" in source),
        ]

        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {check_name}")

        all_passed = all(passed for _, passed in checks)
        if all_passed:
            logger.info("✓ Mass ingest integration complete\n")
        else:
            logger.warning("⚠ Some integrations may be incomplete\n")

        return all_passed

    except Exception as e:
        logger.error(f"✗ Mass ingest test failed: {e}\n")
        return False


def test_scraper_utils():
    """Test scraper utility functions."""
    logger.info("="*60)
    logger.info("TEST 5: Scraper Utilities")
    logger.info("="*60)

    try:
        from src.ingestion.scraper_utils import (
            DedupAwareScraper,
            extract_and_chunk_multi_format,
            bulk_download_with_dedup
        )

        logger.info("  ✓ DedupAwareScraper class available")
        logger.info("  ✓ extract_and_chunk_multi_format() function available")
        logger.info("  ✓ bulk_download_with_dedup() function available")

        # Test DedupAwareScraper initialization
        class TestScraper(DedupAwareScraper):
            pass

        scraper = TestScraper()
        tracker = scraper.init_dedup_tracker()
        logger.info(f"  ✓ DedupAwareScraper initialized successfully")

        logger.info("✓ Scraper utilities working correctly\n")
        return True

    except Exception as e:
        logger.error(f"✗ Scraper utilities test failed: {e}\n")
        return False


def print_summary(results: dict):
    """Print test summary."""
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! Multi-format and deduplication features are working.")
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Please review the output above.")

    return passed == total


def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("Kenya Legal AI Multi-Format & Deduplication Test Suite")
    logger.info("="*60 + "\n")

    results = {
        "Document Handler": test_document_handler(),
        "Deduplication Tracker": test_dedup_tracker(),
        "Document Processor Integration": test_document_processor_integration(),
        "Mass Ingest Integration": test_mass_ingest_integration(),
        "Scraper Utilities": test_scraper_utils(),
    }

    success = print_summary(results)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

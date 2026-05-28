"""
Kenya Legal AI — Multi-Format Document Handler
================================================
Handles extraction of text from multiple document formats:
- PDF (via PyMuPDF)
- DOCX (via python-docx)
- HTML (via BeautifulSoup)
- XML (via lxml)
- TXT (plain text)

Provides format detection, error handling, and graceful fallback.
"""

import logging
from pathlib import Path
from typing import Optional, Union
import re

import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from lxml import etree

logger = logging.getLogger(__name__)


class DocumentHandler:
    """Multi-format document text extraction handler."""

    SUPPORTED_FORMATS = {'.pdf', '.docx', '.html', '.xml', '.txt', '.htm'}

    def __init__(self):
        """Initialize document handler."""
        self.logger = logging.getLogger(__name__)

    def detect_format(self, file_path: Union[str, Path]) -> Optional[str]:
        """Detect document format from file extension."""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        if suffix in self.SUPPORTED_FORMATS:
            return suffix.lstrip('.')
        return None

    def extract_text(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract text from a document in any supported format.
        Returns None if extraction fails.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return None

        doc_format = self.detect_format(file_path)
        if not doc_format:
            self.logger.warning(f"Unsupported format: {file_path.suffix}")
            return None

        try:
            if doc_format == 'pdf':
                return self._extract_pdf(file_path)
            elif doc_format == 'docx':
                return self._extract_docx(file_path)
            elif doc_format in ('html', 'htm'):
                return self._extract_html(file_path)
            elif doc_format == 'xml':
                return self._extract_xml(file_path)
            elif doc_format == 'txt':
                return self._extract_txt(file_path)
        except Exception as e:
            self.logger.error(f"Error extracting {doc_format} from {file_path}: {e}")
            # Attempt fallback to raw text reading
            try:
                return self._extract_txt(file_path)
            except Exception as fallback_error:
                self.logger.error(f"Fallback text extraction failed: {fallback_error}")
                return None

        return None

    def _extract_pdf(self, file_path: Path) -> Optional[str]:
        """Extract text from PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num, page in enumerate(doc, start=1):
                text += page.get_text()
                # Add page break marker
                if page_num < len(doc):
                    text += f"\n[Page {page_num} end]\n"
            doc.close()
            return text if text.strip() else None
        except Exception as e:
            self.logger.error(f"PDF extraction error: {e}")
            raise

    def _extract_docx(self, file_path: Path) -> Optional[str]:
        """Extract text from DOCX using python-docx."""
        try:
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
        except ImportError:
            self.logger.error("python-docx not installed. Install with: pip install python-docx")
            raise

        try:
            doc = Document(file_path)
            text = []

            for element in doc.element.body:
                if isinstance(element, Paragraph):
                    para_text = element.text.strip()
                    if para_text:
                        text.append(para_text)
                elif isinstance(element, Table):
                    # Extract table text
                    for row in element.rows:
                        row_text = [cell.text.strip() for cell in row.cells]
                        text.append(" | ".join(row_text))

            return "\n\n".join(text) if text else None
        except Exception as e:
            self.logger.error(f"DOCX extraction error: {e}")
            raise

    def _extract_html(self, file_path: Path) -> Optional[str]:
        """Extract text from HTML using BeautifulSoup."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'noscript']):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up excessive whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text if text.strip() else None
        except Exception as e:
            self.logger.error(f"HTML extraction error: {e}")
            raise

    def _extract_xml(self, file_path: Path) -> Optional[str]:
        """Extract text from XML using lxml."""
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()

            # Extract all text content
            text_elements = []
            for element in root.iter():
                if element.text:
                    text_elements.append(element.text.strip())
                if element.tail:
                    text_elements.append(element.tail.strip())

            text = '\n'.join(elem for elem in text_elements if elem)
            return text if text.strip() else None
        except Exception as e:
            self.logger.error(f"XML extraction error: {e}")
            raise

    def _extract_txt(self, file_path: Path) -> Optional[str]:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text if text.strip() else None
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
                return text if text.strip() else None
            except Exception as e:
                self.logger.error(f"TXT extraction error: {e}")
                raise

    def get_format_stats(self, directory: Path) -> dict:
        """Get statistics on file formats in a directory."""
        stats = {fmt: 0 for fmt in self.SUPPORTED_FORMATS}
        stats['unknown'] = 0

        if not directory.exists():
            return stats

        for file_path in directory.rglob('*'):
            if file_path.is_file():
                fmt = self.detect_format(file_path)
                if fmt:
                    stats[f'.{fmt}'] = stats.get(f'.{fmt}', 0) + 1
                else:
                    stats['unknown'] += 1

        return {k: v for k, v in stats.items() if v > 0}


# Global instance for convenience
_handler = None


def get_document_handler() -> DocumentHandler:
    """Get or create global document handler instance."""
    global _handler
    if _handler is None:
        _handler = DocumentHandler()
    return _handler


def extract_text_from_file(file_path: Union[str, Path]) -> Optional[str]:
    """
    Convenience function to extract text from any supported document format.

    Args:
        file_path: Path to the document

    Returns:
        Extracted text or None if extraction fails
    """
    handler = get_document_handler()
    return handler.extract_text(file_path)

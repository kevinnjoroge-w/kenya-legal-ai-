"""
Kenya Legal AI — Document Processor
=====================================
Handles cleaning, chunking, and preparing legal documents for embedding.
Uses legal-aware splitting strategies that respect document structure
(sections, articles, paragraphs) rather than naive character splitting.
"""

import json
import logging
import re
import hashlib
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List
import fitz # PyMuPDF

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of a legal document ready for embedding."""
    chunk_id: str
    document_id: str
    document_title: str
    document_type: str              # constitution | act | judgment | legal_notice
    source: str                     # kenya_law | laws_africa | judiciary
    text: str
    metadata: dict = field(default_factory=dict)
    # Structural context
    section: str = ""               # e.g., "Part II", "Section 27", "Article 10"
    court: str = ""
    date: str = ""
    citation: str = ""
    chunk_index: int = 0
    total_chunks: int = 0


class LegalDocumentProcessor:
    """Process and chunk legal documents for the RAG pipeline."""

    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.processed_dir = Path(settings.processed_data_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean raw legal text by removing artifacts and normalizing whitespace.
        """
        # Remove excessive whitespace but keep paragraph structure
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        # Remove page numbers and headers/footers common in legal PDFs
        text = re.sub(r"\n\s*Page\s+\d+\s+of\s+\d+\s*\n", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)

        # Normalize legal formatting
        text = re.sub(r"(?<=\w)\s*—\s*(?=\w)", " — ", text)

        return text.strip()

    @staticmethod
    def _generate_chunk_id(document_id: str, chunk_index: int) -> str:
        """Generate a deterministic chunk ID."""
        raw = f"{document_id}:chunk:{chunk_index}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _generate_document_id(source: str, identifier: str) -> str:
        """Generate a deterministic document ID."""
        raw = f"{source}:{identifier}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _split_by_legal_sections(self, text: str) -> list[str]:
        """
        Split text at legal section boundaries (Articles, Sections, Parts).
        Falls back to paragraph splitting if no legal structure is found.
        """
        # Try splitting by major legal section markers
        section_patterns = [
            # Constitution articles
            r"(?=\n\s*Article\s+\d+)",
            # Act sections
            r"(?=\n\s*Section\s+\d+)",
            # Parts and chapters
            r"(?=\n\s*(?:PART|Part|CHAPTER|Chapter)\s+[IVXLCDM\d]+)",
            # Numbered paragraphs in judgments
            r"(?=\n\s*\d+\.\s+[A-Z])",
        ]

        for pattern in section_patterns:
            sections = re.split(pattern, text)
            sections = [s.strip() for s in sections if s.strip()]
            if len(sections) > 1:
                return sections

        # Fallback: split by double newlines (paragraphs)
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def _merge_small_sections(
        self, sections: list[str], min_size: int = 200
    ) -> list[str]:
        """Merge sections that are too small to be useful standalone."""
        merged = []
        buffer = ""

        for section in sections:
            if len(buffer) + len(section) < min_size:
                buffer += "\n\n" + section if buffer else section
            else:
                if buffer:
                    merged.append(buffer)
                buffer = section

        if buffer:
            merged.append(buffer)

        return merged

    def _split_large_section(self, text: str) -> list[str]:
        """Split a section that exceeds chunk_size into smaller pieces."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def chunk_document(
        self,
        text: str,
        document_id: str,
        document_title: str,
        document_type: str,
        source: str,
        metadata: Optional[dict] = None,
    ) -> list[DocumentChunk]:
        """
        Chunk a legal document using legal-aware splitting.

        Args:
            text: Raw document text
            document_id: Unique document identifier
            document_title: Title of the document
            document_type: Type (constitution, act, judgment, legal_notice)
            source: Data source (kenya_law, laws_africa, judiciary)
            metadata: Additional metadata dict

        Returns:
            List of DocumentChunk objects
        """
        # Clean the text
        cleaned = self.clean_text(text)

        if not cleaned:
            logger.warning(f"Empty document after cleaning: {document_id}")
            return []

        # Split into legal sections
        sections = self._split_by_legal_sections(cleaned)

        # Merge very small sections
        sections = self._merge_small_sections(sections)

        # Split oversized sections
        all_chunks_text = []
        for section in sections:
            all_chunks_text.extend(self._split_large_section(section))

        # Detect section headers for each chunk
        section_pattern = re.compile(
            r"^(Article\s+\d+|Section\s+\d+|"
            r"(?:PART|Part|CHAPTER|Chapter)\s+[IVXLCDM\d]+)",
            re.MULTILINE,
        )

        # Build DocumentChunk objects
        chunks = []
        total = len(all_chunks_text)

        for idx, chunk_text in enumerate(all_chunks_text):
            section_match = section_pattern.search(chunk_text)
            section_label = section_match.group(0) if section_match else ""

            chunk = DocumentChunk(
                chunk_id=self._generate_chunk_id(document_id, idx),
                document_id=document_id,
                document_title=document_title,
                document_type=document_type,
                source=source,
                text=chunk_text,
                metadata=metadata or {},
                section=section_label,
                court=metadata.get("court", "") if metadata else "",
                date=metadata.get("date", "") if metadata else "",
                citation=metadata.get("citation", "") if metadata else "",
                chunk_index=idx,
                total_chunks=total,
            )
            chunks.append(chunk)

        logger.info(
            f"Chunked '{document_title[:50]}' into {len(chunks)} chunks "
            f"(avg {sum(len(c.text) for c in chunks) // max(len(chunks), 1)} chars)"
        )
        return chunks

    def save_chunks(self, chunks: list[DocumentChunk], filename: str) -> Path:
        """Save chunks to a JSONL file."""
        output_path = self.processed_dir / f"{filename}.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
        return output_path

    def process_judgment_file(
        self, text_path: Path, metadata_path: Path
    ) -> list[DocumentChunk]:
        """
        Process a scraped judgment file into chunks.

        Args:
            text_path: Path to the judgment text file
            metadata_path: Path to the metadata JSON file

        Returns:
            List of DocumentChunk objects
        """
        text = text_path.read_text(encoding="utf-8")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        doc_id = self._generate_document_id(
            "kenya_law", metadata.get("case_number", text_path.stem)
        )

        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=metadata.get("title", ""),
            document_type="judgment",
            source="kenya_law",
            metadata=metadata,
        )

    def process_legislation_file(
        self, html_path: Path, metadata_path: Path
    ) -> list[DocumentChunk]:
        """
        Process a downloaded legislation HTML file into chunks.

        Args:
            html_path: Path to the legislation HTML file
            metadata_path: Path to the metadata JSON file

        Returns:
            List of DocumentChunk objects
        """
        from bs4 import BeautifulSoup

        html = html_path.read_text(encoding="utf-8")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        # Extract text from HTML
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n", strip=True)

        doc_id = self._generate_document_id(
            "laws_africa", metadata.get("frbr_uri", html_path.stem)
        )

        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=metadata.get("title", ""),
            document_type="act",
            source="laws_africa",
            metadata=metadata,
        )

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file using PyMuPDF."""
        text = ""
        try:
            with fitz.open(str(pdf_path)) as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return text

    def process_judiciary_file(self, doc_dir: Path) -> list[DocumentChunk]:
        """Process a judiciary document (PDF + metadata) into chunks."""
        pdf_path = doc_dir / "document.pdf"
        meta_path = doc_dir / "metadata.json"
        
        if not pdf_path.exists() or not meta_path.exists():
            return []
            
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        text = self.extract_text_from_pdf(pdf_path)
        
        doc_id = self._generate_document_id("judiciary", doc_dir.name)
        
        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=metadata.get("title", ""),
            document_type="legal_notice", # Default for practice directions/orders
            source="judiciary",
            metadata=metadata,
        )


def process_all_documents():
    """Process all downloaded raw documents into chunks."""
    settings = get_settings()
    processor = LegalDocumentProcessor()
    all_chunks = []

    # Process Kenya Law cases
    cases_dir = Path(settings.raw_data_dir) / "kenya_law" / "cases"
    if cases_dir.exists():
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                text_path = case_dir / "judgment.txt"
                meta_path = case_dir / "metadata.json"
                if text_path.exists() and meta_path.exists():
                    chunks = processor.process_judgment_file(text_path, meta_path)
                    all_chunks.extend(chunks)

    # Process Laws.Africa legislation
    laws_dir = Path(settings.raw_data_dir) / "laws_africa"
    if laws_dir.exists():
        for work_dir in laws_dir.iterdir():
            if work_dir.is_dir():
                html_path = work_dir / "content.html"
                meta_path = work_dir / "metadata.json"
                if html_path.exists() and meta_path.exists():
                    chunks = processor.process_legislation_file(html_path, meta_path)
                    all_chunks.extend(chunks)

    # Process Judiciary documents
    judiciary_dir = Path(settings.raw_data_dir) / "judiciary" / "documents"
    if judiciary_dir.exists():
        for doc_dir in judiciary_dir.iterdir():
            if doc_dir.is_dir():
                chunks = processor.process_judiciary_file(doc_dir)
                all_chunks.extend(chunks)
                
    # Process Kenya Law Gazettes
    gazettes_dir = Path(settings.raw_data_dir) / "kenya_law" / "gazettes"
    if gazettes_dir.exists():
        for doc_dir in gazettes_dir.iterdir():
            if doc_dir.is_dir():
                # Gazettes are also PDFs usually
                chunks = processor.process_judiciary_file(doc_dir) # Reuse the PDF processor
                for c in chunks:
                    c.source = "kenya_law"
                    c.document_type = "legal_notice"
                all_chunks.extend(chunks)

    # Save all chunks
    if all_chunks:
        processor.save_chunks(all_chunks, "all_documents")

    logger.info(f"Total chunks processed: {len(all_chunks)}")
    return all_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_all_documents()

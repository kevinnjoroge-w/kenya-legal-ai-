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
from pathlib import Pathvenv) ┌─[✗]─[defk@parrot]─[~/kenya-legal-ai-]
└──╼ $python -m scripts.run_pipeline --step index

╔═══════════════════════════════════════════════════════╗
║           Kenya Legal AI — Data Pipeline              ║
║         Constitution • Acts • Judgments • More         ║
╚═══════════════════════════════════════════════════════╝

2026-03-26 14:21:07,398 | __main__ | INFO | ============================================================
2026-03-26 14:21:07,398 | __main__ | INFO | STEP 3: EMBEDDING & INDEXING
2026-03-26 14:21:07,399 | __main__ | INFO | ============================================================
Traceback (most recent call last):
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 72, in map_httpcore_exceptions
yield
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 236, in handle_request
resp = self._pool.handle_request(req)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_sync/connection_pool.py", line 256, in handle_request
raise exc from None
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_sync/connection_pool.py", line 236, in handle_request
response = connection.handle_request(
pool_request.request
)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_sync/connection.py", line 101, in handle_request
raise exc
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_sync/connection.py", line 78, in handle_request
stream = self._connect(request)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_sync/connection.py", line 124, in _connect
stream = self._network_backend.connect_tcp(**kwargs)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_backends/sync.py", line 207, in connect_tcp
with map_exceptions(exc_map):
~~~~~~~~~~~~~~^^^^^^^^^
File "/usr/lib/python3.13/contextlib.py", line 162, in __exit__
self.gen.throw(value)
~~~~~~~~~~~~~~^^^^^^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
raise to_exc(exc) from exc
httpcore.ConnectError: [Errno -3] Temporary failure in name resolution

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 106, in send_inner
response = self._client.send(request)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_client.py", line 926, in send
response = self._send_handling_auth(
request,
...<2 lines>...
history=[],
)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_client.py", line 954, in _send_handling_auth
response = self._send_handling_redirects(
request,
follow_redirects=follow_redirects,
history=history,
)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_client.py", line 991, in _send_handling_redirects
response = self._send_single_request(request)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_client.py", line 1027, in _send_single_request
response = transport.handle_request(request)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 235, in handle_request
with map_httpcore_exceptions():
~~~~~~~~~~~~~~~~~~~~~~~^^
File "/usr/lib/python3.13/contextlib.py", line 162, in __exit__
self.gen.throw(value)
~~~~~~~~~~~~~~^^^^^^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 89, in map_httpcore_exceptions
raise mapped_exc(message) from exc
httpx.ConnectError: [Errno -3] Temporary failure in name resolution

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "<frozen runpy>", line 198, in _run_module_as_main
File "<frozen runpy>", line 88, in _run_code
File "/home/defk/kenya-legal-ai-/scripts/run_pipeline.py", line 120, in <module>
main()
~~~~^^
File "/home/defk/kenya-legal-ai-/scripts/run_pipeline.py", line 114, in main
step_index()
~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/scripts/run_pipeline.py", line 82, in step_index
index_all_processed_documents()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/src/embedding/embedding_service.py", line 499, in index_all_processed_documents
service.index_from_jsonl(chunks_file)
~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
File "/home/defk/kenya-legal-ai-/src/embedding/embedding_service.py", line 385, in index_from_jsonl
self.ensure_collection()
~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/src/embedding/embedding_service.py", line 117, in ensure_collection
collections = self.qdrant.get_collections().collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/qdrant_client.py", line 2076, in get_collections
return self._client.get_collections(**kwargs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/qdrant_remote.py", line 2597, in get_collections
self.http.collections_api.get_collections().result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api/collections_api.py", line 1335, in get_collections
return self._build_for_get_collections()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api/collections_api.py", line 432, in _build_for_get_collections
return self.api_client.request(
~~~~~~~~~~~~~~~~~~~~~~~^
type_=m.InlineResponse2004,
^^^^^^^^^^^^^^^^^^^^^^^^^^^
...<2 lines>...
headers=headers if headers else None,
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
)
^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 79, in request
return self.send(request, type_)
~~~~~~~~~^^^^^^^^^^^^^^^^
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 96, in send
response = self.middleware(request, self.send_inner)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 205, in __call__
return call_next(request)
File "/home/defk/kenya-legal-ai-/venv/lib/python3.13/site-packages/qdrant_client/http/api_client.py", line 108, in send_inner
raise ResponseHandlingException(e)
qdrant_client.http.exceptions.ResponseHandlingException: [Errno -3] Temporary failure in name resolution
(venv) ┌─[✗]─[defk@parrot]─[~/kenya-legal-ai-]
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
        """Save chunks to a JSONL file (overwrites existing)."""
        output_path = self.processed_dir / f"{filename}.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
        return output_path

    def append_chunk_to_file(self, chunk: DocumentChunk, output_path: Path):
        """Append a single chunk to the JSONL file."""
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

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

    def process_generic_kenyalaw_dir(
        self, doc_dir: Path, doc_type: str, pdf_names: tuple = ("document.pdf", "bill.pdf", "decision.pdf", "hansard.pdf", "content.pdf")
    ) -> list[DocumentChunk]:
        """Process a generic KenyaLaw document directory (PDF/Text + metadata) into chunks."""
        meta_path = doc_dir / "metadata.json"
        if not meta_path.exists():
            return []
            
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        
        text_path = doc_dir / "content.txt"
        if text_path.exists():
            text = text_path.read_text(encoding="utf-8")
        else:
            text = ""
            for pdf_name in pdf_names:
                pdf_path = doc_dir / pdf_name
                if pdf_path.exists():
                    text = self.extract_text_from_pdf(pdf_path)
                    break
                    
        if not text:
            return []
            
        doc_id = self._generate_document_id("kenya_law", doc_dir.name)
        title = metadata.get("title", doc_dir.name.replace("_", " "))
        
        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=title,
            document_type=doc_type,
            source="kenya_law",
            metadata=metadata,
        )

    def process_lsk_file(self, pdf_path: Path) -> list[DocumentChunk]:
        """Process an LSK document (PDF only, no metadata) into chunks."""
        if not pdf_path.exists():
            return []
            
        text = self.extract_text_from_pdf(pdf_path)
        
        title = pdf_path.stem.replace("-", " ").replace("_", " ")
        doc_id = self._generate_document_id("lsk", pdf_path.stem)
        
        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=title,
            document_type="guideline",
            source="lsk",
            metadata={"title": title, "filename": pdf_path.name},
        )

    def process_cipit_file(self, filepath: Path) -> list[DocumentChunk]:
        """Process a CIPIT document (PDF or HTML) into chunks."""
        if not filepath.exists():
            return []
            
        is_pdf = filepath.suffix.lower() == ".pdf"
        
        if is_pdf:
            text = self.extract_text_from_pdf(filepath)
        else:
            from bs4 import BeautifulSoup
            html = filepath.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            
        title = filepath.stem.replace("-", " ").replace("_", " ")
        doc_id = self._generate_document_id("cipit", filepath.stem)
        
        return self.chunk_document(
            text=text,
            document_id=doc_id,
            document_title=title,
            document_type="judgment",
            source="cipit",
            metadata={"title": title, "filename": filepath.name},
        )


def process_all_documents(output_filename: str = "all_documents"):
    """
    Process all downloaded raw documents into chunks using a streaming approach
     to keep memory usage low.
    """
    settings = get_settings()
    processor = LegalDocumentProcessor()
    output_path = Path(settings.processed_data_dir) / f"{output_filename}.jsonl"
    
    # Initialize/Clear the output file
    with open(output_path, "w", encoding="utf-8") as f:
        pass
    
    total_chunks = 0
    total_docs = 0

    # 1. Process Laws.Africa legislation (Primary Source for Statutes)
    laws_dir = Path(settings.raw_data_dir) / "laws_africa"
    if laws_dir.exists():
        logger.info("Processing Laws.Africa documents...")
        for work_dir in laws_dir.iterdir():
            if work_dir.is_dir():
                html_path = work_dir / "content.html"
                meta_path = work_dir / "metadata.json"
                if html_path.exists() and meta_path.exists():
                    chunks = processor.process_legislation_file(html_path, meta_path)
                    for c in chunks:
                        processor.append_chunk_to_file(c, output_path)
                    total_chunks += len(chunks)
                    total_docs += 1

    # 2. Process Kenya Law cases
    cases_dir = Path(settings.raw_data_dir) / "kenya_law" / "cases"
    if cases_dir.exists():
        logger.info("Processing Kenya Law cases...")
        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                text_path = case_dir / "judgment.txt"
                meta_path = case_dir / "metadata.json"
                if text_path.exists() and meta_path.exists():
                    chunks = processor.process_judgment_file(text_path, meta_path)
                    for c in chunks:
                        processor.append_chunk_to_file(c, output_path)
                    total_chunks += len(chunks)
                    total_docs += 1

    # 3. Process Judiciary documents
    judiciary_dir = Path(settings.raw_data_dir) / "judiciary" / "documents"
    if judiciary_dir.exists():
        logger.info("Processing Judiciary documents...")
        for doc_dir in judiciary_dir.iterdir():
            if doc_dir.is_dir():
                chunks = processor.process_judiciary_file(doc_dir)
                for c in chunks:
                    processor.append_chunk_to_file(c, output_path)
                total_chunks += len(chunks)
                total_docs += 1
                
    # 4. Process Kenya Law Gazettes
    gazettes_dir = Path(settings.raw_data_dir) / "kenya_law" / "gazettes"
    if gazettes_dir.exists():
        logger.info("Processing Kenya Law Gazettes...")
        for doc_dir in gazettes_dir.iterdir():
            if doc_dir.is_dir():
                chunks = processor.process_judiciary_file(doc_dir)
                for c in chunks:
                    c.source = "kenya_law"
                    c.document_type = "legal_notice"
                    processor.append_chunk_to_file(c, output_path)
                if chunks:
                    total_chunks += len(chunks)
                    total_docs += 1

    # 4.1 Process Kenya Law Bills
    bills_dir = Path(settings.raw_data_dir) / "kenya_law" / "bills"
    if bills_dir.exists():
        logger.info("Processing Parliamentary Bills...")
        for meta_path in bills_dir.rglob("metadata.json"):
            chunks = processor.process_generic_kenyalaw_dir(meta_path.parent, "bill")
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            if chunks:
                total_chunks += len(chunks)
                total_docs += 1

    # 4.2 Process Kenya Law Tribunals
    tribunals_dir = Path(settings.raw_data_dir) / "kenya_law" / "tribunals"
    if tribunals_dir.exists():
        logger.info("Processing Tribunal Decisions...")
        for meta_path in tribunals_dir.rglob("metadata.json"):
            chunks = processor.process_generic_kenyalaw_dir(meta_path.parent, "judgment")
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            if chunks:
                total_chunks += len(chunks)
                total_docs += 1

    # 4.3 Process Practice Notes
    practice_notes_dir = Path(settings.raw_data_dir) / "kenya_law" / "practice_notes"
    if practice_notes_dir.exists():
        logger.info("Processing Practice Notes...")
        for meta_path in practice_notes_dir.rglob("metadata.json"):
            chunks = processor.process_generic_kenyalaw_dir(meta_path.parent, "legal_notice")
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            if chunks:
                total_chunks += len(chunks)
                total_docs += 1

    # 4.4 Process Hansard Debates
    hansard_dir = Path(settings.raw_data_dir) / "kenya_law" / "hansard"
    if hansard_dir.exists():
        logger.info("Processing Hansard Debates...")
        for meta_path in hansard_dir.rglob("metadata.json"):
            chunks = processor.process_generic_kenyalaw_dir(meta_path.parent, "hansard")
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            if chunks:
                total_chunks += len(chunks)
                total_docs += 1

    # 4.5 Process County Legislation
    county_dir = Path(settings.raw_data_dir) / "kenya_law" / "county"
    if county_dir.exists():
        logger.info("Processing County Legislation...")
        for meta_path in county_dir.rglob("metadata.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                doc_type_raw = meta.get("doc_type", "act")
                doc_type = "act" if doc_type_raw == "acts" else ("bill" if doc_type_raw == "bills" else "legal_notice")
            except Exception:
                doc_type = "act"
                
            chunks = processor.process_generic_kenyalaw_dir(meta_path.parent, doc_type)
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            if chunks:
                total_chunks += len(chunks)
                total_docs += 1

    # 5. Process LSK documents
    lsk_dir = Path(settings.raw_data_dir) / "lsk"
    if lsk_dir.exists():
        logger.info("Processing LSK documents...")
        for pdf_path in lsk_dir.glob("*.pdf"):
            chunks = processor.process_lsk_file(pdf_path)
            for c in chunks:
                processor.append_chunk_to_file(c, output_path)
            total_chunks += len(chunks)
            total_docs += 1

    # 6. Process CIPIT documents
    cipit_dir = Path(settings.raw_data_dir) / "cipit"
    if cipit_dir.exists():
        logger.info("Processing CIPIT documents...")
        for filepath in cipit_dir.iterdir():
            if filepath.is_file() and filepath.suffix in [".pdf", ".html"]:
                chunks = processor.process_cipit_file(filepath)
                for c in chunks:
                    processor.append_chunk_to_file(c, output_path)
                total_chunks += len(chunks)
                total_docs += 1

    logger.info(f"Final Batch Processing Stats: {total_docs} documents, {total_chunks} total chunks.")
    return total_chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_all_documents()

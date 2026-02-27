"""
Kenya Legal AI — Embedding Service
====================================
Handles generating embeddings and storing/querying the Qdrant vector database.
Supports both OpenAI and open-source embedding models.
"""

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional
import os

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from openai import OpenAI
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.config.settings import get_settings
from src.processing.document_processor import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages embedding generation and vector database operations."""

    def __init__(self):
        settings = get_settings()

        self.embedding_provider = settings.embedding_provider
        self.embedding_model = settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension

        # Initialize appropriate client
        if self.embedding_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is missing in settings")
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        elif self.embedding_provider == "google":
            if not settings.google_api_key:
                logger.error("GOOGLE_API_KEY is missing. Check your .env or production environment variables.")
                raise ValueError(
                    "GOOGLE_API_KEY is not set. If you are on Render, add it to your environment variables."
                )
            genai.configure(api_key=settings.google_api_key)
            self.google_model = settings.embedding_model
        elif self.embedding_provider == "huggingface":
            if SentenceTransformer is None:
                raise ImportError(
                    "sentence-transformers is not installed. Please run: pip install sentence-transformers"
                )
            logger.info(f"Loading HuggingFace model: {settings.embedding_model}")
            self.hf_model = SentenceTransformer(settings.embedding_model)

        # Initialize Qdrant client
        if settings.qdrant_api_key:
            # For Qdrant Cloud: handle both full URLs and hostnames
            host = settings.qdrant_host
            if host.startswith(("http://", "https://")):
                url = host
            else:
                # Default to port 443 for Cloud if not specified as 6333
                port = settings.qdrant_port if settings.qdrant_port != 6333 else 443
                url = f"https://{host}:{port}"

            self.qdrant = QdrantClient(
                url=url,
                api_key=settings.qdrant_api_key,
            )
        else:
            self.qdrant = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=60.0,
            )

        self.collection_name = settings.qdrant_collection
        
        self.qdrant_cloud = None
        if hasattr(settings, "qdrant_cloud_host") and settings.qdrant_cloud_host and hasattr(settings, "qdrant_cloud_api_key") and settings.qdrant_cloud_api_key:
            self.qdrant_cloud = QdrantClient(
                url=settings.qdrant_cloud_host,
                api_key=settings.qdrant_cloud_api_key,
                timeout=60.0,
            )

    def ensure_collection(self):
        """Create the Qdrant collection if it doesn't exist."""
        collections = self.qdrant.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                f"Created Qdrant collection '{self.collection_name}' "
                f"(dim={self.embedding_dimension})"
            )
        else:
            logger.info(f"Collection '{self.collection_name}' already exists")

        # Do the same for Cloud if configured
        if self.qdrant_cloud:
            collections_cloud = self.qdrant_cloud.get_collections().collections
            exists_cloud = any(c.name == self.collection_name for c in collections_cloud)
            if not exists_cloud:
                self.qdrant_cloud.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Cloud Qdrant collection '{self.collection_name}'")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as a list of floats
        """
        if self.embedding_provider == "openai":
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        elif self.embedding_provider == "google":
            result = genai.embed_content(
                model=self.google_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        elif self.embedding_provider == "huggingface" and self.hf_model:
            return self.hf_model.encode(text).tolist()
        return []

    def generate_embeddings_batch(
        self, texts: list[str], batch_size: int = 100
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        if self.embedding_provider == "openai":
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Embedded OpenAI batch {i // batch_size + 1}")
            return all_embeddings
            
        elif self.embedding_provider == "google":
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                
                # Simple retry logic for rate limits
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = genai.embed_content(
                            model=self.google_model,
                            content=batch,
                            task_type="retrieval_document",
                        )
                        all_embeddings.extend(result["embedding"])
                        logger.info(f"Embedded Google batch {i // batch_size + 1}")
                        break
                    except Exception as e:
                        if "429" in str(e) and attempt < max_retries - 1:
                            wait_time = 60  # Wait a full minute if rate limited
                            logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                        else:
                            raise e
            return all_embeddings
            
        elif self.embedding_provider == "huggingface" and self.hf_model:
            logger.info(f"Embedding {len(texts)} texts with HuggingFace ({settings.embedding_model})")
            embeddings = self.hf_model.encode(texts, batch_size=batch_size, show_progress_bar=False)
            return embeddings.tolist()
            
        return []

    def index_chunks(self, chunks: list[DocumentChunk], batch_size: int = 50):
        """
        Embed and index document chunks into Qdrant.

        Args:
            chunks: List of DocumentChunk objects to index
            batch_size: Number of chunks to process per batch
        """
        self.ensure_collection()

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.text for chunk in batch]

            # Generate embeddings
            embeddings = self.generate_embeddings_batch(texts)

            # Build Qdrant points
            points = []
            for chunk, embedding in zip(batch, embeddings):
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "document_type": chunk.document_type,
                    "source": chunk.source,
                    "text": chunk.text,
                    "section": chunk.section,
                    "court": chunk.court,
                    "date": chunk.date,
                    "citation": chunk.citation,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                }

                points.append(
                    PointStruct(
                        id=hash(chunk.chunk_id) & 0x7FFFFFFFFFFFFFFF,  # Positive int64
                        vector=embedding,
                        payload=payload,
                    )
                )

            # Upsert to Qdrant
            try:
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
            except Exception as e:
                logger.error(f"Failed to upsert to local Qdrant: {e}")
            
            # Upsert to Cloud Qdrant
            if self.qdrant_cloud:
                try:
                    self.qdrant_cloud.upsert(
                        collection_name=self.collection_name,
                        points=points,
                    )
                except Exception as e:
                    logger.error(f"Failed to upsert to Cloud Qdrant: {e}")
            
            # Small delay between batches to respect rate limits
            if self.embedding_provider == "google":
                time.sleep(2)

            logger.info(
                f"Indexed batch {i // batch_size + 1}"
                f"/{(len(chunks) - 1) // batch_size + 1} "
                f"({len(points)} points)"
            )

        logger.info(f"Total chunks indexed: {len(chunks)}")

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_type: Optional[str] = None,
        court: Optional[str] = None,
    ) -> list[dict]:
        """
        Search the vector database for relevant document chunks.

        Args:
            query: Search query text
            top_k: Number of results to return
            document_type: Filter by document type (constitution, act, judgment)
            court: Filter by court name

        Returns:
            List of search result dictionaries with score and payload
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)

        # Build filters
        conditions = []
        if document_type:
            conditions.append(
                FieldCondition(
                    key="document_type",
                    match=MatchValue(value=document_type),
                )
            )
        if court:
            conditions.append(
                FieldCondition(
                    key="court",
                    match=MatchValue(value=court),
                )
            )

        search_filter = Filter(must=conditions) if conditions else None

        # Search Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
        )

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "document_title": hit.payload.get("document_title", ""),
                "document_type": hit.payload.get("document_type", ""),
                "section": hit.payload.get("section", ""),
                "court": hit.payload.get("court", ""),
                "date": hit.payload.get("date", ""),
                "citation": hit.payload.get("citation", ""),
                "source": hit.payload.get("source", ""),
                "chunk_id": hit.payload.get("chunk_id", ""),
            }
            for hit in results
        ]

    def get_collection_info(self) -> dict:
        """Get information about the current Qdrant collection."""
        try:
            info = self.qdrant.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            return {"error": str(e)}


def index_all_processed_documents():
    """Index all processed document chunks into Qdrant."""
    settings = get_settings()
    service = EmbeddingService()

    # Load processed chunks
    chunks_file = Path(settings.processed_data_dir) / "all_documents.jsonl"
    if not chunks_file.exists():
        logger.error(f"No processed chunks found at {chunks_file}")
        logger.error("Run document processing first: python -m src.processing.document_processor")
        return

    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            chunks.append(DocumentChunk(**data))

    logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")

    # Index into Qdrant
    service.index_chunks(chunks)
    logger.info("Indexing complete!")

    # Print collection info
    info = service.get_collection_info()
    logger.info(f"Collection info: {info}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    index_all_processed_documents()

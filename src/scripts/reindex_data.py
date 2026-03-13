"""
Kenya Legal AI — Data Re-indexing Script
========================================
Recreates the Qdrant collection and re-indexes all processed documents
using the configured embedding model (Hugging Face).
"""

import logging
import json
from pathlib import Path
from src.embedding.embedding_service import EmbeddingService
from src.config.settings import get_settings
from src.processing.document_processor import DocumentChunk

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reindex_all():
    settings = get_settings()
    service = EmbeddingService()
    
    logger.info(f"Starting re-indexing with provider: {settings.embedding_provider}, model: {settings.embedding_model}")
    
    # 1. Recreate collection (wipe old vectors, create new with 1024 dim)
    service.recreate_collection()
    
    # 2. Index using streaming from jsonl
    chunks_file = Path(settings.processed_data_dir) / "all_documents.jsonl"
    if not chunks_file.exists():
        logger.error(f"No processed chunks found at {chunks_file}")
        return
        
    logger.info(f"Loading chunks from {chunks_file}...")
    service.index_from_jsonl(chunks_file, batch_size=32)

    # 3. Print collection info
    info = service.get_collection_info()
    logger.info(f"Final collection info: {info}")

if __name__ == "__main__":
    reindex_all()

import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.embedding.embedding_service import EmbeddingService
from src.config.settings import get_settings

def test_local_embeddings():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    logger.info(f"Testing embedding provider: {settings.embedding_provider}")
    logger.info(f"Model: {settings.embedding_model}")
    
    try:
        service = EmbeddingService()
        test_text = "The Constitution of Kenya is the supreme law of the Republic of Kenya."
        
        logger.info("Generating embedding...")
        embedding = service.generate_embedding(test_text)
        
        logger.info(f"Embedding generated! Length: {len(embedding)}")
        
        expected_dim = settings.embedding_dimension
        if len(embedding) == expected_dim:
            logger.info(f"✅ Success! Embedding dimension matches: {len(embedding)}")
        else:
            logger.error(f"❌ Error: Embedding dimension mismatch. Expected {expected_dim}, got {len(embedding)}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_local_embeddings()

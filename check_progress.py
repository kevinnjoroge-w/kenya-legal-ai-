from src.embedding.embedding_service import EmbeddingService
import logging

logging.basicConfig(level=logging.INFO)
service = EmbeddingService()
info = service.get_collection_info()
print(f"Current Points in Collection: {info.get('points_count', 'Unknown')}")

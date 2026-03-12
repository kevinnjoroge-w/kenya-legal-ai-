import sys
import os
import psutil

process = psutil.Process()
print(f"Memory before: {process.memory_info().rss / 1024 / 1024:.2f} MB")

from src.embedding.embedding_service import EmbeddingService
svc = EmbeddingService()
print("Service initialized")
print(f"Memory after init: {process.memory_info().rss / 1024 / 1024:.2f} MB")

svc.generate_embedding("Test sentence for memory profiling")
print("Embedding generated")
print(f"Memory after model load: {process.memory_info().rss / 1024 / 1024:.2f} MB")

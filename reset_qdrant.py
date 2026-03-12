import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

# We need to recreate the 768-dim collection on both Cloud and Local
collection_name = os.getenv("QDRANT_COLLECTION", "kenya_legal_docs")
dim = int(os.getenv("EMBEDDING_DIMENSION", 768))

def recreate_for_client(client, host_name):
    print(f"Checking {host_name}...")
    try:
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            print(f"Deleting existing collection '{collection_name}' on {host_name}...")
            client.delete_collection(collection_name)
        
        print(f"Creating new collection '{collection_name}' with {dim} dimensions on {host_name}...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print("Success!\n")
    except Exception as e:
        print(f"Error on {host_name}: {e}\n")


cloud_url = os.getenv("QDRANT_CLOUD_HOST")
cloud_api_key = os.getenv("QDRANT_CLOUD_API_KEY")
local_host = os.getenv("QDRANT_HOST")
local_port = int(os.getenv("QDRANT_PORT", 6333))
local_api_key = os.getenv("QDRANT_API_KEY")

if cloud_url and cloud_api_key:
    cloud_client = QdrantClient(url=cloud_url, api_key=cloud_api_key, timeout=30)
    recreate_for_client(cloud_client, "Qdrant Cloud")

if local_host:
    if local_host.startswith("http"):
        local_client = QdrantClient(url=local_host, api_key=local_api_key, timeout=30)
    else:
        local_client = QdrantClient(host=local_host, port=local_port, api_key=local_api_key, timeout=30)
    recreate_for_client(local_client, "Primary Qdrant")

print("Qdrant reset complete.")

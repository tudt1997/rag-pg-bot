import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from typing import List, Dict
import ollama

class VectorStore:
    # TODO: parametrize host and port
    def __init__(self, collection_name: str = "text_embeddings", dim: int = 768):
        self.collection_name = collection_name
        self.dim = dim
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=self.host, port=self.port)
        print(f"Connected to Qdrant at {self.host}:{self.port}")

    def create_index(self, show_fields=False):
        """
        Create a collection with vector parameters suitable for vector search.
        """
        if self.client.collection_exists(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists.")
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE)
        )
        print(f"✅ Collection '{self.collection_name}' has been created.")

        if show_fields:
            print("Qdrant collections store vectors and payloads (metadata).")

    def delete_index(self):
        """
        Delete the collection if it exists.
        """
        if self.client.get_collection(self.collection_name, raise_error=False):
            self.client.delete_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' has been deleted.")

    def upload_embeddings(self, data: List[Dict]):
        """
        Upload a list of documents in the format:
        {
          "chunk_id": str,
          "text": str,
          "source": str,
          "page_number": int,
          "offset": int,
          "embedding": List[float]  # 768 dimensions
        }
        """
        points = [
            PointStruct(
                id=doc["chunk_id"],
                vector=doc["embedding"],
                payload={
                    "text": doc["text"],
                    "source": doc["source"],
                    "page_number": doc["page_number"],
                    "offset": doc["offset"]
                }
            )
            for doc in data
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"Uploaded {len(points)} documents to collection '{self.collection_name}'")

    def semantic_search(self, query_vector, k: int = 5) -> List[Dict]:
        """
        Perform semantic vector search using cosine similarity.
        """
        response = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k
        )
        return [
            {
                "text": hit.payload.get("text"),
                "source": hit.payload.get("source"),
                "page_number": hit.payload.get("page_number"),
                "score": hit.score
            }
            for hit in response
        ]
 
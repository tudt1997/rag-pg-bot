import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from typing import List, Dict
import ollama

class VectorStore:
    def __init__(self, index_name: str = "text_embeddings", dim: int = 768):
        self.index_name = index_name
        self.dim = dim
        self.host = os.getenv("ELASTIC_HOST", "104.43.56.154")
        self.port = os.getenv("ELASTIC_PORT", "9200")
        self.es = Elasticsearch(f"http://{self.host}:{self.port}")
        print(f"Connected to Elasticsearch at {self.host}:{self.port}")
    
    def create_index(self, show_fields=False):
        """
        Create an index with mappings suitable for vector search.
        """
        if self.es.indices.exists(index=self.index_name):
            print(f"Index '{self.index_name}' already exists.")
            return

        mapping = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "text": {"type": "text"},
                    "source": {"type": "keyword"},
                    "page_number": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": self.dim,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }

        self.es.indices.create(index=self.index_name, body=mapping)
        print(f"✅ Index '{self.index_name}' has been created.")

        if show_fields:
            index_info = self.es.indices.get_mapping(index=self.index_name)
            fields = index_info[self.index_name]['mappings']['properties']
            print("Fields in the index:")
            for field_name, field_info in fields.items():
                print(f" - {field_name}: {field_info['type']}")

    def delete_index(self):
        """
        Delete the index if it exists.
        """
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            print(f"Index '{self.index_name}' has been deleted.")

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
        actions = [
            {
                "_index": self.index_name,
                "_source": doc
            }
            for doc in data
        ]
        bulk(self.es, actions)
        print(f"Uploaded {len(actions)} documents to index '{self.index_name}'")

    def semantic_search(self, question, k: int = 5) -> List[Dict]:
        """
        Perform semantic vector search using cosine similarity.
        """
        query = {
            "size": k,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": question}
                    }
                }
            }
        }

        response = self.es.search(index=self.index_name, body=query)
        return [
            {
                "text": hit["_source"].get("text"),
                "source": hit["_source"].get("source"),
                "page_number": hit["_source"].get("page_number"),
                "score": hit["_score"]
            }
            for hit in response["hits"]["hits"]
        ]

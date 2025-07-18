# This code for deletion of index in elasticsearch

from elasticsearch import Elasticsearch
import os

# Connect to Elasticsearch
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "104.43.56.154")
ELASTIC_PORT = os.getenv("ELASTIC_PORT", "9200")
es = Elasticsearch(f"http://{ELASTIC_HOST}:{ELASTIC_PORT}")

# Index name
index_name = "text_embeddings"

# Delete the index if it exists
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"Index '{index_name}' has been deleted successfully.")
else:
    print(f"Index '{index_name}' does not exist.")

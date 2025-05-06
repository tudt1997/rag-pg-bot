from rag_system.components.search.search_base import SearchBase
from rag_system.services.vector_store import VectorStore

class ElasticSearch(SearchBase): 
    def __init__(self): 
        self.search_client = VectorStore()

    def search(self, index_name, question):
        return self.search_client.semantic_search(question)
    
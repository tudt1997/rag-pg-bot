# Description: This file contains the test cases for the loader module using Ollama + Elasticsearch.

from rag_system.components.loaders.local_loader import LocalOCRPDFLoader
from rag_system.components.chunkers.fixed_size_chunker import LangchainCompatibleChunker
from rag_system.components.embedders.embedder import Embedder

def test_loader(url):
    loader = LocalOCRPDFLoader()
    data_chunks_by_page = loader.load(url)
    assert len(data_chunks_by_page) > 0

    chunker = LangchainCompatibleChunker()
    chunked_data = chunker.chunk(data_chunks_by_page)

    embedder = Embedder(index_name="text_embeddings")  
    embedder.embed_and_load(chunked_data)

if __name__ == "__main__":
    url = "uploads/Nghị định 13 về bảo vệ dữ liệu cá nhân.pdf" 
    test_loader(url)

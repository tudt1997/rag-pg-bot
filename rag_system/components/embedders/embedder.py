from .embedder_base import EmbedderBase
from typing import List
from rag_system.core.data_chunk import DataChunk
from rag_system.services.vector_store import VectorStore
from rag_system.services.embedding import EmbeddingClient

class Embedder(EmbedderBase):
    def __init__(self, index_name: str = "text_embeddings"):
        """
        Initialize the embedder with a embedding client and Elasticsearch vector store.
        """
        # Initialize embedding client
        self.embed_client = EmbeddingClient()
        self.index_name = index_name
        # Initialize Elasticsearch vector store with the appropriate dimensionality
        self.vector_store = VectorStore(
            index_name=index_name,
            dim=self.embed_client.embedding_dimensions
        )

    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the provided text using Halong embedding model.

        Args:
            text (str): The input text to embed.

        Returns:
            List[float]: The embedding vector.
        """
        return self.embed_client.generate_embeddings(text)
    
    def embed_and_load(self, data: List[DataChunk]) -> None:
        """
        Embed a list of DataChunk objects and load the results into Elasticsearch.

        Args:
            data (List[DataChunk]): A list of DataChunk instances to embed and store.
        """
        try:
            # Create the index if it does not exist
            self.vector_store.create_index()

            # Extract content and compute embeddings
            contents = [chunk.content for chunk in data]
            embeddings = [self.embed(content) for content in contents]
            print(f"Generated {len(embeddings)} embeddings")

            # Prepare documents for bulk upload
            documents = []
            for i, chunk in enumerate(data):
                record = chunk.to_dictionary()
                record["text"] = record.get("content", "")
                record["embedding"] = embeddings[i]
                record["chunk_id"] = record.get("chunk_id", f"chunk_{i}")
                documents.append(record)

            # Upload embeddings to Elasticsearch
            self.vector_store.upload_embeddings(documents)
            print("Successfully uploaded embedded data to Elasticsearch.")

        except Exception as e:
            print(f"Error while embedding and uploading: {e}")

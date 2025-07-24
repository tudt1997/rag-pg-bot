from .embedder_base import EmbedderBase
from typing import List, Generator
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
            collection_name=index_name,
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
    
    def embed_and_load_one(self, chunk: DataChunk, chunk_index: int = 0) -> None:
        """
        Embed a single DataChunk object and load the result into Elasticsearch.

        Args:
            chunk (DataChunk): A DataChunk instance to embed and store.
            chunk_index (int): Index for tracking purposes if chunk_id is not set.
        """
        try:
            # Create the index if it does not exist
            self.vector_store.create_index()

            # Generate embedding for this chunk
            print(f"Generating embedding for chunk from source: {chunk.source}")
            embedding = self.embed(chunk.content)
            print(f"Successfully generated embedding for chunk from source: {chunk.source}")

            # Prepare document for upload
            record = chunk.to_dictionary()
            record["text"] = record.get("content", "")
            record["embedding"] = embedding
            record["chunk_id"] = record.get("chunk_id", f"chunk_{chunk_index}")

            # Upload embedding to Elasticsearch
            self.vector_store.upload_embeddings([record])
            print(f"Successfully uploaded embedded data for chunk from source: {chunk.source}")

        except Exception as e:
            print(f"Error while embedding and uploading chunk from source {chunk.source}: {e}")
    
    def process_chunks_one_by_one(self, chunks_generator: Generator[DataChunk, None, None], total_estimate: int = None) -> None:
        """
        Process and embed chunks one by one from a generator.

        Args:
            chunks_generator: A generator that yields DataChunk objects one at a time.
            total_estimate: An optional estimate of the total number of chunks (if known).
        """
        try:
            # Create the index if it does not exist
            self.vector_store.create_index()
            
            chunk_count = 0
            start_time = __import__('time').time()
            
            for chunk in chunks_generator:
                # Log progress information
                if total_estimate:
                    progress_percent = (chunk_count / total_estimate) * 100
                    print(f"Processing chunk {chunk_count+1}/{total_estimate} ({progress_percent:.1f}%)")
                else:
                    print(f"Processing chunk #{chunk_count+1}")
                
                # Process the chunk
                self.embed_and_load_one(chunk, chunk_count)
                chunk_count += 1
                
                # Calculate and display rate information every 5 chunks
                if chunk_count % 5 == 0:
                    elapsed = __import__('time').time() - start_time
                    rate = chunk_count / elapsed if elapsed > 0 else 0
                    print(f"Progress: {chunk_count} chunks processed in {elapsed:.1f} seconds ({rate:.2f} chunks/sec)")
            
            # Final statistics
            total_time = __import__('time').time() - start_time
            avg_time_per_chunk = total_time / chunk_count if chunk_count > 0 else 0
            print(f"Successfully processed and embedded {chunk_count} chunks one by one.")
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Average time per chunk: {avg_time_per_chunk:.2f} seconds")
            
        except Exception as e:
            print(f"Error while processing chunks one by one: {e}")

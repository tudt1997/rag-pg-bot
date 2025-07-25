import time

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

    def _process_batch(self, batch: List[DataChunk], current_count: int = None, start_time: float = None) -> None:
        """
        Helper method to process and embed a batch of chunks.

        Args:
            batch: List of DataChunk objects to process
            current_count: Current count of total processed chunks (optional, for progress tracking)
            start_time: Start time of processing (optional, for rate calculation)
        """
        try:
            # Create the index if it does not exist
            self.vector_store.create_index()

            print(f"\nProcessing batch of {len(batch)} chunks...")

            # Extract content and compute embeddings in batch
            contents = [chunk.content for chunk in batch]
            embeddings = [self.embed(content) for content in contents]
            print(f"Generated {len(embeddings)} embeddings")

            # Prepare documents for bulk upload
            documents = []
            for i, chunk in enumerate(batch):
                chunk_index = (current_count - len(batch) + i) if current_count else i
                record = chunk.to_dictionary()
                record["text"] = record.get("content", "")
                record["embedding"] = embeddings[i]
                record["chunk_id"] = record.get("chunk_id", f"chunk_{chunk_index}")
                documents.append(record)

            # Upload batch to Elasticsearch
            self.vector_store.upload_embeddings(documents)

            # Calculate and display rate information if timing data provided
            if current_count and start_time:
                elapsed = time.time() - start_time
                rate = current_count / elapsed if elapsed > 0 else 0
                print(f"Batch complete: {len(batch)} chunks processed")
                print(f"Current rate: {rate:.2f} chunks/sec")
            else:
                print("Successfully uploaded embedded data to Elasticsearch.")

        except Exception as e:
            print(f"Error processing batch: {e}")

    def embed_and_load(self, data: List[DataChunk]) -> None:
        """
        Embed a list of DataChunk objects and load the results into Elasticsearch.

        Args:
            data (List[DataChunk]): A list of DataChunk instances to embed and store.
        """
        self._process_batch(data)

    def process_chunks_in_batch(
        self,
        chunks_generator: Generator[DataChunk, None, None],
        batch_size: int = 100,
        total_estimate: int = None,
    ) -> None:
        """
        Process and embed chunks in batches from a generator.

        Args:
            chunks_generator: A generator that yields DataChunk objects one at a time.
            batch_size: Number of chunks to process in each batch (default: 100)
            total_estimate: An optional estimate of the total number of chunks (if known)
        """
        try:
            # Create the index if it does not exist
            self.vector_store.create_index()

            chunk_count = 0
            start_time = time.time()
            current_batch = []

            for chunk in chunks_generator:
                current_batch.append(chunk)
                chunk_count += 1

                # Process batch when it reaches batch_size
                if len(current_batch) >= batch_size:
                    self._process_batch(current_batch, chunk_count, start_time)
                    current_batch = []  # Reset batch

                # Log progress for total estimation
                if total_estimate and chunk_count % batch_size == 0:
                    progress_percent = (chunk_count / total_estimate) * 100
                    print(
                        f"Overall progress: {chunk_count}/{total_estimate} ({progress_percent:.1f}%)"
                    )

            # Process any remaining chunks
            if current_batch:
                self._process_batch(current_batch, chunk_count, start_time)

            # Final statistics
            total_time = __import__("time").time() - start_time
            avg_time_per_chunk = total_time / chunk_count if chunk_count > 0 else 0
            print(f"\nProcessing complete:")
            print(f"Total chunks processed: {chunk_count}")
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Average time per chunk: {avg_time_per_chunk:.2f} seconds")

        except Exception as e:
            print(f"Error while processing chunks in batches: {e}")

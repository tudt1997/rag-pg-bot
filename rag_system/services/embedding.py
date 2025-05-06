from sentence_transformers import SentenceTransformer

class EmbeddingClient:
    def __init__(self, model_name: str = "hiieu/halong_embedding"):
        """
        Initialize the Halong Embedding client.

        Args:
            model_name (str): Hugging Face repository name of the Halong embedding model.
        """
        self.model_name = model_name
        self.embedder = SentenceTransformer(self.model_name, trust_remote_code=True)
        self.embedding_dimensions = self.embedder.get_sentence_embedding_dimension()

    def generate_embeddings(self, text: str) -> list:
        """
        Generate a fixed-size embedding vector for the given text.

        Args:
            text (str): The input text to be embedded.

        Returns:
            list: A 1-D list representing the embedding vector.
        """
        # Encode and return as a Python list
        return self.embedder.encode(text).tolist()

    def get_parameters(self) -> dict:
        """
        Retrieve the current model parameters.

        Returns:
            dict: A dictionary containing the model name and embedding dimensions.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimensions": self.embedding_dimensions
        }


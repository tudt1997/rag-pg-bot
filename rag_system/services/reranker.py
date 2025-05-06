from sentence_transformers import CrossEncoder
from typing import List

class RankerClient:
    def __init__(self, model_name: str = "itdainb/PhoRanker", device: str = "cpu"):
        """
        Initialize the PhoRanker reranker with a CrossEncoder model.
        """
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, texts: List[str]) -> List[float]:
        """
        Given a query and a list of texts, return a list of relevance scores.
        """
        if not texts:
            return []
        pairs = [(query, text) for text in texts]
        scores = self.model.predict(pairs)
        return scores.tolist()

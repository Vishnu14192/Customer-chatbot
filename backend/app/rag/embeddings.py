import os
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:

    def __init__(
        self,
        model_name: str | None = None
    ):
        # Use a local sentence-transformers model for embeddings to avoid external API usage.
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL_NAME",
            "all-MiniLM-L6-v2"
        )

        self.model = SentenceTransformer(self.model_name)

    def embed_documents(self, texts):
        # returns numpy array of shape (len(texts), dim)
        vectors = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return np.array(vectors, dtype=np.float32)

    def embed_query(self, query):
        vec = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)[0]
        return np.array(vec, dtype=np.float32)
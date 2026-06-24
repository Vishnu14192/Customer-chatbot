import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


class EmbeddingService:

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None
    ):
        load_dotenv()

        self.model_name = model_name or os.getenv(
            "OPENAI_RAG_EMBEDDING_MODEL",
            "text-embedding-3-small"
        )

        resolved_api_key = api_key or os.getenv(
            "OPENAI_API_KEY"
        )

        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Set it in your environment or backend/.env"
            )

        self.client = OpenAI(
            api_key=resolved_api_key
        )

    def embed_documents(self, texts):
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )

        vectors = [
            item.embedding
            for item in response.data
        ]

        return np.array(vectors, dtype=np.float32)

    def embed_query(self, query):
        response = self.client.embeddings.create(
            model=self.model_name,
            input=query
        )

        return np.array(
            response.data[0].embedding,
            dtype=np.float32
        )
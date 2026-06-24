import math
import os
import threading

from sentence_transformers import CrossEncoder


class ChunkReranker:

    _model_cache: dict[str, CrossEncoder] = {}
    _cache_lock = threading.Lock()

    def __init__(self):
        self.model_name = os.getenv(
            "RERANKER_MODEL_NAME",
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

        self.device = os.getenv(
            "RERANKER_DEVICE",
            "cpu"
        )

        # Keep small vector-distance signal as tie-breaker.
        self.cross_encoder_weight = 0.85
        self.semantic_weight = 0.15

        self.model = self._get_or_create_model(
            self.model_name,
            self.device
        )

    @classmethod
    def _get_or_create_model(
        cls,
        model_name: str,
        device: str
    ) -> CrossEncoder:
        cache_key = f"{model_name}::{device}"

        with cls._cache_lock:
            if cache_key not in cls._model_cache:
                cls._model_cache[cache_key] = CrossEncoder(
                    model_name,
                    device=device,
                    max_length=512
                )

            return cls._model_cache[cache_key]

    def _normalize_cross_encoder_score(
        self,
        raw_score: float
    ) -> float:
        # CrossEncoder returns logits; convert to [0, 1].
        return 1.0 / (1.0 + math.exp(-raw_score))

    def _semantic_score(self, distance: float) -> float:
        return 1.0 / (1.0 + max(distance, 0.0))

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int
    ) -> list[dict]:

        if not chunks:
            return []

        query_doc_pairs = [
            (query, chunk.get("document", ""))
            for chunk in chunks
        ]

        raw_scores = self.model.predict(
            query_doc_pairs,
            batch_size=16,
            show_progress_bar=False
        )

        scored = []
        for chunk, raw_score in zip(chunks, raw_scores):
            distance = float(chunk.get("distance", 0.0))

            cross_encoder_score = (
                self._normalize_cross_encoder_score(
                    float(raw_score)
                )
            )

            semantic_score = self._semantic_score(distance)

            rerank_score = (
                self.cross_encoder_weight * cross_encoder_score
                + self.semantic_weight * semantic_score
            )

            item = dict(chunk)
            item["cross_encoder_score"] = round(
                cross_encoder_score,
                6
            )
            item["rerank_score"] = round(rerank_score, 6)
            scored.append(item)

        scored.sort(
            key=lambda item: item["rerank_score"],
            reverse=True
        )

        return scored[:top_k]
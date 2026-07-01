import re
import os
from collections import Counter
from pathlib import Path

from app.rag.embeddings import EmbeddingService
from app.rag.reranker import ChunkReranker
from app.rag.vector_store import VectorStore
from app.rag.ingestion_pipeline import IngestionPipeline


class Retriever:

    def __init__(self):

        self.embedding_service = EmbeddingService()

        self.vector_store = VectorStore()

        self.reranker = ChunkReranker()

        self.max_distance = 1.6

        self.relative_margin = 0.25

        self.vector_weight = 0.7

        self.keyword_weight = 0.3

        self.min_keyword_score = 0.05

        # Confidence gates to avoid attributing unrelated queries to docs.
        self.min_rerank_score = float(
            os.getenv("RAG_MIN_RERANK_SCORE", "0.56")
        )
        self.min_cross_encoder_score = float(
            os.getenv("RAG_MIN_CROSS_ENCODER_SCORE", "0.54")
        )
        self.min_keyword_accept_score = float(
            os.getenv("RAG_MIN_KEYWORD_ACCEPT_SCORE", "0.08")
        )

        self._ensure_documents_available()

    def _ensure_documents_available(self) -> None:
        try:
            if self.vector_store.count() > 0:
                return

            docs_dir = (
                Path(__file__).resolve().parent.parent.parent
                / "data"
                / "docs"
            )

            if not docs_dir.exists():
                return

            pipeline = IngestionPipeline()
            pipeline.ingest_directory(str(docs_dir))
        except Exception:
            # Keep retrieval service available even if ingestion fails.
            return

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", (text or "").lower())

    def _keyword_score(self, query: str, document: str) -> float:
        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(document)

        if not query_tokens or not doc_tokens:
            return 0.0

        query_counts = Counter(query_tokens)
        doc_counts = Counter(doc_tokens)

        overlap_count = sum(
            min(doc_counts[token], query_counts[token])
            for token in query_counts
            if token in doc_counts
        )

        if overlap_count == 0:
            return 0.0

        matched_unique = sum(
            1 for token in query_counts
            if token in doc_counts
        )

        coverage = overlap_count / len(query_tokens)
        unique_coverage = matched_unique / len(query_counts)

        score = (0.7 * coverage) + (0.3 * unique_coverage)
        return max(0.0, min(score, 1.0))

    def _candidate_key(self, item: dict) -> str:
        metadata = item.get("metadata") or {}
        source = metadata.get("source", "")
        chunk_id = metadata.get("chunk_id", "")
        document = item.get("document", "")

        if source != "" and chunk_id != "":
            return f"{source}::{chunk_id}"

        return f"{source}::{document[:120]}"

    def _vector_candidates(self, query_embedding, top_n: int) -> list[dict]:
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_n,
            include=["documents", "metadatas", "distances"]
        )

        distances = (results.get("distances") or [[]])[0]
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]

        if not distances:
            return []

        best_distance = distances[0]

        filtered = []
        for index, distance in enumerate(distances):
            if distance > self.max_distance:
                continue

            if distance > (best_distance + self.relative_margin):
                continue

            filtered.append(
                {
                    "document": documents[index],
                    "metadata": metadatas[index],
                    "distance": float(distance),
                    "vector_score": 1.0 / (1.0 + max(float(distance), 0.0)),
                    "keyword_score": 0.0
                }
            )

        if filtered:
            return filtered

        # If absolute thresholds are too strict for the active distance metric,
        # still keep the closest vector matches as candidates.
        fallback_count = min(top_n, len(distances))

        for index in range(fallback_count):
            distance = float(distances[index])
            filtered.append(
                {
                    "document": documents[index],
                    "metadata": metadatas[index],
                    "distance": distance,
                    "vector_score": 1.0 / (1.0 + max(distance, 0.0)),
                    "keyword_score": 0.0
                }
            )

        return filtered

    def _keyword_candidates(self, query: str, top_n: int) -> list[dict]:
        stored = self.vector_store.collection.get(
            include=["documents", "metadatas"]
        )

        documents = stored.get("documents") or []
        metadatas = stored.get("metadatas") or []

        scored = []
        for document, metadata in zip(documents, metadatas):
            keyword_score = self._keyword_score(query, document)
            if keyword_score < self.min_keyword_score:
                continue

            scored.append(
                {
                    "document": document,
                    "metadata": metadata,
                    "distance": 1.0 - keyword_score,
                    "vector_score": 0.0,
                    "keyword_score": keyword_score
                }
            )

        scored.sort(
            key=lambda item: item["keyword_score"],
            reverse=True
        )

        return scored[:top_n]

    def _fuse_candidates(
        self,
        vector_candidates: list[dict],
        keyword_candidates: list[dict]
    ) -> list[dict]:
        fused = {}

        for item in vector_candidates:
            key = self._candidate_key(item)
            fused[key] = {
                "document": item["document"],
                "metadata": item["metadata"],
                "distance": item["distance"],
                "vector_score": item["vector_score"],
                "keyword_score": 0.0,
                "hybrid_score": self.vector_weight * item["vector_score"]
            }

        for item in keyword_candidates:
            key = self._candidate_key(item)
            if key not in fused:
                fused[key] = {
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "distance": item["distance"],
                    "vector_score": 0.0,
                    "keyword_score": item["keyword_score"],
                    "hybrid_score": self.keyword_weight * item["keyword_score"]
                }
                continue

            fused[key]["keyword_score"] = max(
                fused[key]["keyword_score"],
                item["keyword_score"]
            )

            fused[key]["distance"] = min(
                fused[key]["distance"],
                item["distance"]
            )

            fused[key]["hybrid_score"] = (
                (self.vector_weight * fused[key]["vector_score"])
                + (self.keyword_weight * fused[key]["keyword_score"])
            )

        ranked = list(fused.values())
        ranked.sort(
            key=lambda item: item["hybrid_score"],
            reverse=True
        )

        return ranked

    def _empty_response(self):
        return {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "reranked_chunks": []
        }

    def _is_confident_chunk(self, item: dict) -> bool:
        rerank_score = float(item.get("rerank_score", 0.0))
        cross_encoder_score = float(item.get("cross_encoder_score", 0.0))
        keyword_score = float(item.get("keyword_score", 0.0))

        passes_rerank = rerank_score >= self.min_rerank_score
        has_supporting_signal = (
            cross_encoder_score >= self.min_cross_encoder_score
            or keyword_score >= self.min_keyword_accept_score
        )

        return passes_rerank and has_supporting_signal

    def search(
        self,
        query: str,
        top_k: int = 3,
        candidate_k: int = 8
    ):

        query_embedding = (
            self.embedding_service
            .embed_query(query)
        )

        pool_size = max(top_k, candidate_k)

        vector_candidates = self._vector_candidates(
            query_embedding=query_embedding,
            top_n=pool_size
        )

        keyword_candidates = self._keyword_candidates(
            query=query,
            top_n=pool_size
        )

        fused_candidates = self._fuse_candidates(
            vector_candidates=vector_candidates,
            keyword_candidates=keyword_candidates
        )

        if not fused_candidates:
            return self._empty_response()

        candidate_chunks = fused_candidates[:pool_size]

        reranked_chunks = self.reranker.rerank(
            query=query,
            chunks=candidate_chunks,
            top_k=top_k
        )

        confident_chunks = [
            item
            for item in reranked_chunks
            if self._is_confident_chunk(item)
        ]

        if not confident_chunks:
            return self._empty_response()

        return {
            "documents": [[
                item["document"]
                for item in confident_chunks
            ]],
            "metadatas": [[
                item["metadata"]
                for item in confident_chunks
            ]],
            "distances": [[
                item["distance"]
                for item in confident_chunks
            ]],
            "reranked_chunks": confident_chunks
        }
"""Personal-memory service with mem0-first strategy and local fallback."""

import os
import re
import uuid
from pathlib import Path

try:
    from mem0 import Memory
    _HAS_MEM0 = True
except Exception:
    Memory = None
    _HAS_MEM0 = False

import chromadb
from app.rag.embeddings import EmbeddingService

_CHROMA_PATH = str(Path(__file__).parent.parent.parent / "mem0_storage")


class MemoryService:
    """Stores and retrieves user-level personal facts across conversations."""

    def __init__(self):
        """
        Attempt to configure mem0 to use local models (Ollama for LLM and
        SentenceTransformers for embeddings). If mem0 is not available or the
        requested providers are not supported, fall back to a simple
        Chromadb-backed memory that uses the local `EmbeddingService`.
        """

        # Preferred local model settings (can be overridden via env vars)
        self.ollama_model = os.getenv("MEM0_OLLAMA_MODEL", "Qwen3:1.7B")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.embedding_model = "nomic-embed-text"

        # Try mem0 first
        if _HAS_MEM0:
            try:
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": "flipkart_memory",
                            "path": _CHROMA_PATH,
                            "embedding_model_dims": 768
                        }
                    },
                    "llm": {
                        "provider": "ollama",
                        "config": {
                            "model": self.ollama_model,
                            "ollama_base_url": self.ollama_base_url
                        }
                    },
                    "embedder": {
                        "provider": "ollama",
                        "config": {
                            "model": "nomic-embed-text",
                            "ollama_base_url": self.ollama_base_url
                        }
                    }
                }

                # Memory.from_config may raise if providers are unsupported
                self.memory = Memory.from_config(config)
                self._use_mem0 = True
                return
            except Exception:
                # Fall through to local implementation
                self._use_mem0 = False

        # Fallback: Chromadb-backed local memory using local embeddings
        self._use_mem0 = False
        self.embedder = EmbeddingService(self.embedding_model)

        self.client = chromadb.PersistentClient(
            path=_CHROMA_PATH
        )

        self.collection = self.client.get_or_create_collection(
            name="flipkart_memory"
        )

    def add_memory(self, user_id, message):
        """Persist one or more extracted personal facts for the user."""
        facts = self.extract_personal_facts(message)

        if not facts:
            return

        if getattr(self, "_use_mem0", False):
            # mem0 memory API
            for fact in facts:
                self.memory.add(fact, user_id=user_id)
            return

        embeddings = self.embedder.embed_documents(facts)
        ids = [f"{user_id}_{uuid.uuid4().hex}" for _ in facts]
        metadatas = [{"user_id": user_id} for _ in facts]

        self.collection.add(ids=ids, documents=facts, embeddings=[e.tolist() for e in embeddings], metadatas=metadatas)

    def search_memory(self, query, user_id, top_k: int = 5):
        """Retrieve top personal memories relevant to the current query."""
        if getattr(self, "_use_mem0", False):
            results = self.memory.search(query=query, filters={"user_id": user_id})
            return results.get("results", [])

        q_emb = self.embedder.embed_query(query).tolist()

        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"]
        )

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        out = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            if meta.get("user_id") != user_id:
                continue
            out.append({"memory": doc, "metadata": meta, "distance": float(dist)})

        return out

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "")).strip()

    def extract_personal_facts(self, message: str) -> list[str]:
        """Extract personal profile facts from free-form user text."""
        text = self._normalize_text(message)
        if not text:
            return []

        # If it looks like a pure question, avoid storing it as a memory fact.
        lower = text.lower()
        if text.endswith("?") and not re.search(r"\b(i am|i'm|my name is|i like|i love|i studied|i work)\b", lower):
            return []

        pieces = re.split(r"[.;\n]+|\band\b", text, flags=re.IGNORECASE)

        personal_fact_patterns = [
            r"\bmy name is\b",
            r"\bi am\b",
            r"\bi'm\b",
            r"\bi was\b",
            r"\bi live in\b",
            r"\bi am from\b",
            r"\bi like\b",
            r"\bi love\b",
            r"\bi enjoy\b",
            r"\bi work\b",
            r"\bi study\b",
            r"\bi studied\b",
            r"\bmy hobby\b",
            r"\bmy hobbies\b",
            r"\bmy favorite\b",
        ]

        support_intent_words = [
            "order",
            "refund",
            "return",
            "shipment",
            "shipping",
            "delivery",
            "cancel",
            "replacement",
            "product",
            "payment",
            "invoice",
        ]

        facts = []

        for piece in pieces:
            candidate = self._normalize_text(piece).strip(",")
            if len(candidate) < 6:
                continue

            c_lower = candidate.lower()
            has_personal_pattern = any(
                re.search(pattern, c_lower)
                for pattern in personal_fact_patterns
            )

            if not has_personal_pattern:
                continue

            # Avoid storing transactional support statements as profile memory.
            if any(word in c_lower for word in support_intent_words):
                continue

            facts.append(candidate)

        # Stable de-dup while preserving order.
        seen = set()
        unique_facts = []
        for fact in facts:
            key = fact.lower()
            if key in seen:
                continue
            seen.add(key)
            unique_facts.append(fact)

        return unique_facts

    def is_personal_query(self, message: str) -> bool:
        """Detect profile/memory lookups such as 'who am i' and 'what do I like'."""
        text = self._normalize_text(message).lower()

        if not text:
            return False

        patterns = [
            r"\bwho am i\b",
            r"\bwho i'm\b",
            r"\bwho i am\b",
            r"\bwhat is my name\b",
            r"\bdo you remember me\b",
            r"\bwhat do i like\b",
            r"\bwhere do i live\b",
            r"\bwhat did i tell you about myself\b",
            r"\bmy profile\b",
            r"\babout me\b",
        ]

        return any(re.search(pattern, text) for pattern in patterns)

    def is_profile_summary_query(self, message: str) -> bool:
        """Detect requests asking what the assistant remembers about the user."""
        text = self._normalize_text(message).lower()

        if not text:
            return False

        patterns = [
            r"\bwhat do you remember about me\b",
            r"\bwhat do you know about me\b",
            r"\bwhat have i told you about me\b",
            r"\btell me what you remember about me\b",
            r"\bshow my profile\b",
            r"\bmy profile summary\b",
            r"\bsummarize what you know about me\b",
        ]

        return any(re.search(pattern, text) for pattern in patterns)

    def get_user_memories(self, user_id: str, top_k: int = 30) -> list[str]:
        """Return deduplicated personal memory facts for one user."""
        if getattr(self, "_use_mem0", False):
            # mem0 has search as the stable API surface across versions.
            results = self.memory.search(
                query="personal profile about me",
                filters={"user_id": user_id},
                limit=top_k,
            )
            raw_items = results.get("results", []) if isinstance(results, dict) else []
            candidates = []
            for item in raw_items:
                if isinstance(item, dict):
                    candidates.append(
                        item.get("memory") or item.get("text") or item.get("content") or ""
                    )
            return self._dedupe_facts(candidates)

        results = self.collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"],
            limit=top_k,
        )

        documents = results.get("documents") or []
        return self._dedupe_facts(documents)

    @staticmethod
    def _dedupe_facts(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for item in items:
            fact = (item or "").strip()
            if not fact:
                continue
            key = fact.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(fact)
        return out

    def should_store_memory(self, message):
        """Heuristic gate to decide whether a message contains personal facts."""
        return len(self.extract_personal_facts(message)) > 0
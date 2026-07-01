import os
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
        if getattr(self, "_use_mem0", False):
            # mem0 memory API
            self.memory.add(message, user_id=user_id)
            return

        emb = self.embedder.embed_documents([message])[0].tolist()
        mem_id = f"{user_id}_{uuid.uuid4().hex}"
        metadata = {"user_id": user_id}

        self.collection.add(
            ids=[mem_id],
            documents=[message],
            embeddings=[emb],
            metadatas=[metadata]
        )

    def search_memory(self, query, user_id, top_k: int = 5):
        if getattr(self, "_use_mem0", False):
            results = self.memory.search(query=query, filters={"user_id": user_id})
            return results.get("results", [])

        q_emb = self.embedder.embed_query(query).tolist()

        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
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

    def should_store_memory(self, message):
        message = message.lower()

        memory_patterns = [
            "my name is",
            "i am",
            "i live in",
            "my favorite",
            "i like",
            "i work",
            "i study",
        ]

        return any(pattern in message for pattern in memory_patterns)
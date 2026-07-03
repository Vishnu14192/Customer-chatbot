"""ChromaDB wrapper used for storing retrieval chunks."""

from pathlib import Path
import chromadb

_CHROMA_PATH = str(Path(__file__).parent.parent.parent / "chroma_db")


class VectorStore:
    """Provides minimal persistence helpers over a Chroma collection."""

    def __init__(self):
        """Initialize persistent Chroma client and retrieval collection."""

        self.client = chromadb.PersistentClient(
            path=_CHROMA_PATH
        )

        self.collection = (
            self.client.get_or_create_collection(
                name="flipkart_docs"
            )
        )

    def add_documents(
        self,
        ids,
        documents,
        embeddings,
        metadatas
    ):
        """Insert a batch of chunk ids, texts, vectors, and metadata."""

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

    def count(self):
        """Return total number of chunks stored in the collection."""
        return self.collection.count()
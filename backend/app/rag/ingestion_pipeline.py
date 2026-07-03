"""Offline ingestion pipeline that chunks docs, embeds them, and stores vectors."""

from pathlib import Path

from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore


class IngestionPipeline:
    """Coordinates document ingestion into the vector store."""

    def __init__(self):

        self.chunker = DocumentChunker()

        self.embedding_service = EmbeddingService()

        self.vector_store = VectorStore()

    def ingest_directory(
        self,
        docs_dir: str
    ):
        """Ingest all markdown files in a directory into Chroma."""

        docs_path = Path(docs_dir)

        total_chunks = 0

        for file_path in docs_path.glob("*.md"):

            print(f"\nProcessing: {file_path.name}")

            text = file_path.read_text(
                encoding="utf-8"
            )

            chunks = self.chunker.chunk_text(text)

            embeddings = (
                self.embedding_service
                .embed_documents(chunks)
            )

            ids = [
                f"{file_path.stem}_{i}"
                for i in range(len(chunks))
            ]

            # metadata = [
            #     {
            #         "source": file_path.name
            #     }
            #     for _ in chunks
            # ]

            metadata = [
                {
                    "source": file_path.name,
                    "category": file_path.stem,
                    "chunk_id": i
                }
                for i in range(len(chunks))
            ]

            self.vector_store.add_documents(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadata
            )

            print(
                f"Created {len(chunks)} chunks"
            )

            total_chunks += len(chunks)

        print("\nIngestion Complete")
        print(
            f"Total Chunks Stored: {total_chunks}"
        )
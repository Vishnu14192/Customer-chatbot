from pathlib import Path
import chromadb

_CHROMA_PATH = str(Path(__file__).parent.parent.parent / "chroma_db")


class VectorStore:

    def __init__(self):

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

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

    def count(self):
        return self.collection.count()
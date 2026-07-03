"""Text chunking helper for splitting long documents into retrieval units."""

from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Wrapper around RecursiveCharacterTextSplitter with project defaults."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk_text(self, text: str):
        """Split a raw document string into overlapping chunks."""
        return self.splitter.split_text(text)
from dotenv import load_dotenv

from app.rag.ingestion_pipeline import (
    IngestionPipeline
)


if __name__ == "__main__":

    load_dotenv()

    pipeline = IngestionPipeline()

    pipeline.ingest_directory(
        "data/docs"
    )
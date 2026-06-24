import os
from pathlib import Path
from mem0 import Memory

_MEM0_PATH = str(Path(__file__).parent.parent.parent / "mem0_storage")


class MemoryService:

    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Set it in your environment or backend/.env"
            )

        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "flipkart_memory",
                    "path": _MEM0_PATH,
                    "embedding_model_dims": 1536
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": os.getenv(
                        "OPENAI_MEMORY_LLM_MODEL",
                        "gpt-4o-mini"
                    ),
                    "api_key": api_key
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": os.getenv(
                        "OPENAI_EMBEDDING_MODEL",
                        "text-embedding-3-small"
                    ),
                    "api_key": api_key
                }
            }
        }

        self.memory = Memory.from_config(config)

    def add_memory(
        self,
        user_id,
        message
    ):
        self.memory.add(
            message,
            user_id=user_id
        )

    def search_memory(
        self,
        query,
        user_id
    ):

        results = self.memory.search(
            query=query,
            filters={
                "user_id": user_id
            }
        )

        return results["results"]

    def should_store_memory(
        self,
        message
    ):

        message = message.lower()

        memory_patterns = [
            "my name is",
            "i am",
            "i live in",
            "my favorite",
            "i like",
            "i work",
            "i study"
        ]

        return any(
            pattern in message
            for pattern in memory_patterns
        )
import os
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "flipkart_memory",
            "path": "./mem0_storage",
            "embedding_model_dims": 1536
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    }
}

import time

start = time.time()
memory = Memory.from_config(config)
print("Init:", time.time() - start)

start = time.time()
memory.add(
    "My name is Vishnu",
    user_id="vishnu"
)
print("Add:", time.time() - start)

start = time.time()

results = memory.search(
    query="What is my name?",
    filters={
        "user_id": "vishnu"
    }
)
print("Search:", time.time() - start)


print(results)
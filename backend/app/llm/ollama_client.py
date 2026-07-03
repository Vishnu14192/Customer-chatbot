"""Thin Ollama wrapper used by chat service for sync and token streaming."""

import ollama


class OllamaClient:
    """Encapsulates local model calls to Ollama."""

    def __init__(
        self,
        model: str = "Qwen3:1.7b"
    ):
        self.model = model

    def generate(
        self,
        prompt: str
    ) -> str:
        """Generate a full response in one call."""

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    def generate_stream(
        self,
        prompt: str
    ):
        """Yield incremental token chunks for streaming UIs."""

        response_stream = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=True
        )

        for chunk in response_stream:
            token = (
                chunk.get("message", {})
                .get("content", "")
            )

            if token:
                yield token
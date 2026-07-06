"""Thin Ollama wrapper used by chat service for sync and token streaming."""

import os

import ollama


class OllamaClient:
    """Encapsulates local model calls to Ollama."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None
    ):
        self.model = model or os.getenv(
            "OLLAMA_MODEL",
            "Qwen3:1.7b"
        )

        resolved_base_url = base_url or os.getenv("OLLAMA_BASE_URL")

        self.client = ollama.Client(
            host=resolved_base_url
        ) if resolved_base_url else ollama.Client()

    def generate(
        self,
        prompt: str
    ) -> str:
        """Generate a full response in one call."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to reach local Ollama. Ensure Ollama is running and the configured model is available."
            ) from exc

        return response["message"]["content"]

    def generate_stream(
        self,
        prompt: str
    ):
        """Yield incremental token chunks for streaming UIs."""
        try:
            response_stream = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to reach local Ollama. Ensure Ollama is running and the configured model is available."
            ) from exc

        for chunk in response_stream:
            token = (
                chunk.get("message", {})
                .get("content", "")
            )

            if token:
                yield token
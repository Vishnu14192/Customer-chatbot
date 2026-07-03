"""OpenAI wrapper kept for optional cloud model usage."""

import os

from openai import OpenAI


class OpenAIClient:
    """Encapsulates OpenAI responses API calls."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None
    ):
        self.model = model or os.getenv(
            "OPENAI_CHAT_MODEL",
            "gpt-4o-mini"
        )

        resolved_api_key = api_key or os.getenv(
            "OPENAI_API_KEY"
        )

        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Set it in your environment or backend/.env"
            )

        self.client = OpenAI(
            api_key=resolved_api_key
        )

    def generate(
        self,
        prompt: str
    ) -> str:
        """Generate one full answer string from OpenAI."""

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text.strip()
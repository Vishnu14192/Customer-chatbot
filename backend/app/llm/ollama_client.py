import ollama


class OllamaClient:

    def __init__(
        self,
        model: str = "Qwen3:1.7b"
    ):
        self.model = model

    def generate(
        self,
        prompt: str
    ) -> str:

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
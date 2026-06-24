class PromptBuilder:

    @staticmethod
    def build(
        question: str,
        docs: list[str],
        memories: list[str] | None = None,
        history: list[dict] | None = None
    ) -> str:
        memories = memories or []
        history = history or []

        docs_text = "\n\n".join(docs) if docs else ""
        memory_text = "\n".join(memories) if memories else ""

        history_lines = []
        for item in history[-8:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_text = "\n".join(history_lines)

        return f"""
You are Flipkart customer support assistant.

Answer clearly and briefly.
Use the knowledge context when available.
If the answer is not in the provided context, say so and give a safe fallback.

Conversation history:
{history_text}

User memory:
{memory_text}

Knowledge context:
{docs_text}

User question:
{question}

Answer:
""".strip()
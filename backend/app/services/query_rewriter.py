"""Rewrites follow-up user questions into standalone retrieval-friendly queries."""

class QueryRewriter:
    """Uses the configured LLM to rewrite context-dependent questions."""

    def __init__(self, llm):

        self.llm = llm

    def rewrite(
        self,
        question,
        conversation_history
    ):
        """Return a rewritten query string or the original if unchanged."""

        prompt = f"""
You are a query rewriting assistant for a conversational AI chatbot.

Give me a quick response to the user's latest question, making it self-contained and clear, while preserving the user's intent. Use the conversation history to provide context if necessary.

Your task is to rewrite the user's latest question only when necessary.

Rules:

1. If the question already makes sense by itself, return it unchanged.

2. If the question contains references such as:
   - it
   - this
   - that
   - they
   - them
   - those
   - these
   then use the conversation history to make it self-contained.

3. Preserve the user's intent exactly.

4. Do NOT answer the question.

5. Do NOT explain your reasoning.

6. Return only the rewritten query.

Conversation History:
{conversation_history}

Latest Question:
{question}

Rewritten Query:
"""

        rewritten = self.llm.generate(
            prompt
        )

        return rewritten.strip()
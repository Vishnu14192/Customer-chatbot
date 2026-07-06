"""Main orchestration service for retrieval, memory, LLM calls, and persistence."""

import uuid
from collections.abc import Generator

from app.rag.retriever import Retriever
from app.rag.prompt_builder import PromptBuilder
from app.llm.ollama_client import OllamaClient
from app.services.memory_service import MemoryService

from app.services.chat_history_service import (
    ChatHistoryService
)
from app.services.query_rewriter import (
    QueryRewriter
)


class ChatService:
    """Coordinates the full chat pipeline for both sync and streaming modes."""

    def __init__(self):

        self.retriever = Retriever()

        self.llm = OllamaClient()

        self.memory_service = MemoryService()

        self.chat_history = (ChatHistoryService())

        self.query_rewriter = QueryRewriter(self.llm)

    def _validated_query(
        self,
        original_question: str,
        rewritten_question: str
    ) -> str:
        """Reject rewrite outputs that look like answers and keep safe query text."""
        candidate = (
            (rewritten_question or "")
            .strip()
            .strip('"')
        )

        if not candidate:
            return original_question

        lower_candidate = candidate.lower()

        answer_markers = [
            "answer:",
            "assistant:",
            "final answer",
            "here is",
            "here's",
            "i can help",
            "i'm unable"
        ]

        looks_like_answer = any(
            marker in lower_candidate
            for marker in answer_markers
        )

        too_long = len(candidate.split()) > max(
            50,
            len(original_question.split()) * 3
        )

        multiline_answer = (
            "\n" in candidate
            and len(candidate.split()) > 25
        )

        if looks_like_answer or too_long or multiline_answer:
            return original_question

        return candidate

    def _build_chat_plan(
        self,
        user_id: str,
        question: str,
        thread_id: str | None = None
    ) -> dict:
        """Build a normalized execution plan shared by sync and streaming chat."""
        resolved_thread_id = thread_id or str(
            uuid.uuid4()
        )

        history = (
            self.chat_history.get_history(
                user_id,
                thread_id=resolved_thread_id
            )
        )

        rewritten_question = (
            self.query_rewriter.rewrite(
                question,
                history
            )
        )

        effective_question = self._validated_query(
            original_question=question,
            rewritten_question=rewritten_question
        )

        self.chat_history.add_message(
            user_id=user_id,
            thread_id=resolved_thread_id,
            role="user",
            message=question
        )

        summary_keywords = [
            "summarize",
            "summary",
            "what did we discuss",
            "conversation summary"
        ]

        if any(
            word in effective_question.lower()
            for word in summary_keywords
        ):
            history_text = "\n".join(
                [
                    f"{h['role']}: {h['content']}"
                    for h in history
                ]
            )

            prompt = f"""
        Summarize this conversation.

        Give me qucik summary of the conversation below. Do not include any personal information in the summary.

        {history_text}
        """

            return {
                "thread_id": resolved_thread_id,
                "prompt": prompt,
                "sources": [],
                "should_store_memory": False,
                "question": question,
            }

        memory_results = (
            self.memory_service.search_memory(
                effective_question,
                user_id
            )
        )

        profile_summary_query = self.memory_service.is_profile_summary_query(
            effective_question
        )

        if profile_summary_query:
            profile_memories = self.memory_service.get_user_memories(
                user_id=user_id,
                top_k=40
            )

            if profile_memories:
                memory_context = "\n".join(profile_memories)

                prompt = f"""
You are a helpful assistant.

Create a concise personal profile summary using only the stored memory facts below.
Keep it factual and avoid inventing details.
Use 3-6 short bullet points.

STORED MEMORY FACTS:
{memory_context}

USER QUESTION:
{effective_question}

SUMMARY:
"""

                return {
                    "thread_id": resolved_thread_id,
                    "prompt": prompt,
                    "sources": ["memory"],
                    "should_store_memory": False,
                    "question": question,
                }

            prompt = f"""
You are a helpful assistant.

The user asked for a profile summary but no personal memory exists yet.
Respond in one short sentence saying you do not have personal details yet and ask them to share some profile information.

USER QUESTION:
{effective_question}

RESPONSE:
"""

            return {
                "thread_id": resolved_thread_id,
                "prompt": prompt,
                "sources": ["memory"],
                "should_store_memory": False,
                "question": question,
            }

        memories = [
            item.get("memory") or item.get("text") or item.get("content")
            for item in memory_results
            if isinstance(item, dict)
        ]
        memories = [memory for memory in memories if memory]

        is_personal = self.memory_service.is_personal_query(
            effective_question
        )

        should_store_memory = self.memory_service.should_store_memory(question)

        if is_personal and memories:
            memory_context = "\n".join(
                memories
            )

            prompt = f"""
Answer using the memory below.

Give me a quick response to the user's latest question, making it self-contained and clear, while preserving the user's intent. Use the memory context to provide context if necessary.

MEMORY:
{memory_context}

QUESTION:
{effective_question}

ANSWER:
"""

            return {
                "thread_id": resolved_thread_id,
                "prompt": prompt,
                "sources": ["memory"],
                "should_store_memory": False,
                "question": question,
            }

        if is_personal and not memories:
            prompt = f"""
You are a helpful assistant.

The user asked about their personal profile, but there is no stored memory yet.
Respond briefly that you do not have their personal details yet and ask them to share profile information they want you to remember.

USER QUESTION:
{effective_question}

RESPONSE:
"""

            return {
                "thread_id": resolved_thread_id,
                "prompt": prompt,
                "sources": ["memory"],
                "should_store_memory": False,
                "question": question,
            }

        if should_store_memory:
            memory_context = "\n".join(
                self.memory_service.extract_personal_facts(question)
            )

            prompt = f"""
You are a helpful assistant.

The user shared personal information. Acknowledge that you understood it in 1-2 short lines.
Do not invent new details.
Do not switch to Flipkart support fallback messaging.

USER FACTS:
{memory_context}

USER MESSAGE:
{question}

RESPONSE:
"""

            return {
                "thread_id": resolved_thread_id,
                "prompt": prompt,
                "sources": ["memory"],
                "should_store_memory": True,
                "question": question,
            }

        results = self.retriever.search(
            effective_question
        )

        docs = []

        if results["documents"]:
            docs = results["documents"][0]

        if docs:
            prompt = PromptBuilder.build(
                effective_question,
                docs,
                memories,
                history
            )

            metadata_rows = (
                (results.get("metadatas") or [[]])[0]
            )

            sources = sorted(
                {
                    m.get("source", "flipkart_docs")
                    for m in metadata_rows
                    if isinstance(m, dict)
                }
            )

            if not sources:
                sources = ["flipkart_docs"]
        else:
            prompt = PromptBuilder.build(
                effective_question,
                [],
                memories,
                history
            )

            sources = ["llm"]

        return {
            "thread_id": resolved_thread_id,
            "prompt": prompt,
            "sources": sources,
            "should_store_memory": should_store_memory,
            "question": question,
        }

    def chat(
        self,
        user_id: str,
        question: str,
        thread_id: str | None = None
    ):
        """Execute one full chat turn and return a final response payload."""
        plan = self._build_chat_plan(
            user_id=user_id,
            question=question,
            thread_id=thread_id
        )

        answer = self.llm.generate(
            plan["prompt"]
        )

        if plan["should_store_memory"]:
            self.memory_service.add_memory(
                user_id=user_id,
                message=plan["question"]
            )

        self.chat_history.add_message(
            user_id=user_id,
            thread_id=plan["thread_id"],
            role="assistant",
            message=answer,
            sources=plan["sources"]
        )

        return {
            "answer": answer,
            "sources": plan["sources"],
            "thread_id": plan["thread_id"]
        }

    def chat_stream_events(
        self,
        user_id: str,
        question: str,
        thread_id: str | None = None
    ) -> Generator[dict, None, None]:
        """Yield start/token/end events while preserving final answer in history."""
        plan = self._build_chat_plan(
            user_id=user_id,
            question=question,
            thread_id=thread_id
        )

        yield {
            "type": "start",
            "thread_id": plan["thread_id"],
            "sources": plan["sources"]
        }

        chunks = []

        for token in self.llm.generate_stream(
            plan["prompt"]
        ):
            chunks.append(token)

            yield {
                "type": "token",
                "content": token
            }

        answer = "".join(chunks)

        if plan["should_store_memory"]:
            self.memory_service.add_memory(
                user_id=user_id,
                message=plan["question"]
            )

        self.chat_history.add_message(
            user_id=user_id,
            thread_id=plan["thread_id"],
            role="assistant",
            message=answer,
            sources=plan["sources"]
        )

        yield {
            "type": "end",
            "thread_id": plan["thread_id"],
            "sources": plan["sources"]
        }
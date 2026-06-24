from app.rag.retriever import Retriever
from app.rag.prompt_builder import PromptBuilder
from app.llm.openai_client import OpenAIClient
from app.services.memory_service import MemoryService

from app.services.chat_history_service import (
    ChatHistoryService
)
from app.services.query_rewriter import (
    QueryRewriter
)


class ChatService:

    def __init__(self):

        self.retriever = Retriever()

        self.llm = OpenAIClient()

        self.memory_service = MemoryService()

        self.chat_history = (ChatHistoryService())

        self.query_rewriter = QueryRewriter(self.llm)

    def _validated_query(
        self,
        original_question: str,
        rewritten_question: str
    ) -> str:
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

    def chat(
        self,
        user_id: str,
        question: str
    ):
        # ------ History -----
        history = (
            self.chat_history.get_history(
                user_id
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

        print(
            f"\nOriginal: {question}"
        )

        print(
            f"\nRewritten: {rewritten_question}"
        )

        print(
            f"\nEffective: {effective_question}"
        )

        self.chat_history.add_message(
                user_id=user_id,
                role="user",
                message=question
            )

        # -------Summary --------------
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

            answer = self.llm.generate(
                prompt
            )

            return {
                "answer": answer,
                "sources": []
            }

        # ----------------------------------
        # Search Memory
        # ----------------------------------

        memory_results = (
            self.memory_service.search_memory(
                effective_question,
                user_id
            )
        )

        memories = [
            item["memory"]
            for item in memory_results
            if "memory" in item
        ]

        # ----------------------------------
        # Personal Question Detection
        # ----------------------------------

        personal_keywords = [
            "my name",
            "who am i",
            "favorite",
            "where do i live",
            "my city"
        ]

        is_personal = any(
            keyword in effective_question.lower()
            for keyword in personal_keywords
        )

        # ----------------------------------
        # Answer from Memory
        # ----------------------------------

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

            answer = self.llm.generate(
                prompt
            )

            self.chat_history.add_message(
                user_id=user_id,
                role="assistant",
                message=answer
            )

            return {
                "answer": answer,
                "sources": ["memory"]
            }

        # ----------------------------------
        # Search Knowledge Base
        # ----------------------------------
        

        results = self.retriever.search(
            effective_question
        )

        docs = []

        if results["documents"]:

            docs = results["documents"][0]

        # ----------------------------------
        # KB Answer
        # ----------------------------------

        if docs:

            prompt = PromptBuilder.build(
                effective_question,
                docs,
                memories, 
                history
            )

            answer = self.llm.generate(
                prompt
            )


            sources = list(
                set(
                    m["source"]
                    for m in results["metadatas"][0]
                )
            )

        else:

            # ----------------------------------
            # General Chat Fallback
            # ----------------------------------

            prompt = PromptBuilder.build(
                effective_question,
                [],
                memories,
                history
            )

            answer = self.llm.generate(prompt)

            sources = ["llm"]

        # ----------------------------------
        # Save Personal Memories
        # ----------------------------------

        if self.memory_service.should_store_memory(
            question
        ):

            self.memory_service.add_memory(
                user_id=user_id,
                message=question
            )

        self.chat_history.add_message(
                user_id=user_id,
                role="assistant",
                message=answer
            )

        return {
            "answer": answer,
            "sources": sources
        }
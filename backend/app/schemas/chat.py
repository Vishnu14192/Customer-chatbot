"""Pydantic request/response models for chat and thread APIs."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Input payload for chat and chat-stream endpoints."""

    user_id: str

    question: str

    thread_id: str | None = None


class ChatResponse(BaseModel):
    """Standard synchronous chat response payload."""

    answer: str

    sources: list[str]

    thread_id: str


class ChatMessageOut(BaseModel):
    """Serialized message entry returned in thread history."""

    role: str

    content: str

    created_at: str

    sources: list[str] | None = None


class ChatThreadSummary(BaseModel):
    """Compact thread row used in sidebar thread lists."""

    thread_id: str

    title: str

    updated_at: str

    message_count: int


class ChatThreadListResponse(BaseModel):
    """Wrapper response for thread list endpoint."""

    threads: list[ChatThreadSummary]


class ChatThreadHistoryResponse(BaseModel):
    """Wrapper response for one thread's full message history."""

    thread_id: str

    messages: list[ChatMessageOut]


class DeleteThreadResponse(BaseModel):
    """Boolean result payload for delete operations."""

    deleted: bool


class RenameThreadRequest(BaseModel):
    """Input payload for renaming a conversation thread."""

    title: str


class RenameThreadResponse(BaseModel):
    """Boolean result payload for rename operations."""

    renamed: bool
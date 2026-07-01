from pydantic import BaseModel


class ChatRequest(BaseModel):

    user_id: str

    question: str

    thread_id: str | None = None


class ChatResponse(BaseModel):

    answer: str

    sources: list[str]

    thread_id: str


class ChatMessageOut(BaseModel):

    role: str

    content: str

    created_at: str

    sources: list[str] | None = None


class ChatThreadSummary(BaseModel):

    thread_id: str

    title: str

    updated_at: str

    message_count: int


class ChatThreadListResponse(BaseModel):

    threads: list[ChatThreadSummary]


class ChatThreadHistoryResponse(BaseModel):

    thread_id: str

    messages: list[ChatMessageOut]


class DeleteThreadResponse(BaseModel):

    deleted: bool


class RenameThreadRequest(BaseModel):

    title: str


class RenameThreadResponse(BaseModel):

    renamed: bool
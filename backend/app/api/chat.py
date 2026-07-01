import logging
import json
from functools import lru_cache

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    DeleteThreadResponse,
    RenameThreadRequest,
    RenameThreadResponse,
    ChatThreadHistoryResponse,
    ChatThreadListResponse
)

from app.services.chat_service import (
    ChatService
)

router = APIRouter()

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    try:
        return ChatService()
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        ) from exc


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):

    try:

        result = service.chat(
            user_id=request.user_id,
            question=request.question,
            thread_id=request.thread_id
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            thread_id=result["thread_id"]
        )

    except Exception:

        logger.exception("Failed to process chat request")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):

    def event_stream():
        try:
            for event in service.chat_stream_events(
                user_id=request.user_id,
                question=request.question,
                thread_id=request.thread_id
            ):
                yield json.dumps(event) + "\n"
        except Exception as exc:
            logger.exception("Failed to stream chat response")
            yield json.dumps(
                {
                    "type": "error",
                    "message": str(exc)
                }
            ) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson"
    )


@router.get(
    "/chat/threads/{user_id}",
    response_model=ChatThreadListResponse
)
async def list_threads(
    user_id: str,
    service: ChatService = Depends(get_chat_service)
):

    try:
        threads = service.chat_history.get_threads(user_id)

        return ChatThreadListResponse(
            threads=threads
        )

    except Exception:

        logger.exception("Failed to list chat threads")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/chat/threads/{user_id}/{thread_id}",
    response_model=ChatThreadHistoryResponse
)
async def get_thread_history(
    user_id: str,
    thread_id: str,
    service: ChatService = Depends(get_chat_service)
):

    try:
        messages = service.chat_history.get_thread_messages(
            user_id=user_id,
            thread_id=thread_id
        )

        return ChatThreadHistoryResponse(
            thread_id=thread_id,
            messages=messages
        )

    except Exception:

        logger.exception("Failed to get chat thread history")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.delete(
    "/chat/threads/{user_id}/{thread_id}",
    response_model=DeleteThreadResponse
)
async def delete_thread(
    user_id: str,
    thread_id: str,
    service: ChatService = Depends(get_chat_service)
):

    try:
        deleted = service.chat_history.delete_thread(
            user_id=user_id,
            thread_id=thread_id
        )

        return DeleteThreadResponse(
            deleted=deleted
        )

    except Exception:

        logger.exception("Failed to delete chat thread")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.patch(
    "/chat/threads/{user_id}/{thread_id}/title",
    response_model=RenameThreadResponse
)
async def rename_thread(
    user_id: str,
    thread_id: str,
    request: RenameThreadRequest,
    service: ChatService = Depends(get_chat_service)
):

    try:
        title = request.title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

        renamed = service.chat_history.rename_thread(
            user_id=user_id,
            thread_id=thread_id,
            title=title
        )

        return RenameThreadResponse(
            renamed=renamed
        )

    except HTTPException:
        raise
    except Exception:

        logger.exception("Failed to rename chat thread")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
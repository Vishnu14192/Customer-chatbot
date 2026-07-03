"""Chat API routes.

Provides synchronous chat, streaming chat (HTTP and WebSocket), and thread
management endpoints used by the frontend sidebar/history features.
"""

import logging
import json
from functools import lru_cache

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
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
    """Create and cache one ChatService instance for route handlers."""
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
    """Handle one request-response chat call over HTTP."""

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
    """Stream chat events over HTTP NDJSON for token-by-token UI updates."""

    def event_stream():
        """Yield serialized stream events from ChatService."""
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


@router.websocket("/ws/chat")
async def chat_stream_ws(
    websocket: WebSocket,
):
    """Stream chat events over WebSocket while keeping HTTP stream available."""
    await websocket.accept()

    service = get_chat_service()

    try:
        while True:
            payload = await websocket.receive_json()

            user_id = payload.get("user_id")
            question = payload.get("question")
            thread_id = payload.get("thread_id")

            if not user_id or not question:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "user_id and question are required"
                        }
                    )
                )
                continue

            try:
                for event in service.chat_stream_events(
                    user_id=user_id,
                    question=question,
                    thread_id=thread_id
                ):
                    await websocket.send_text(
                        json.dumps(event)
                    )
            except Exception as exc:
                logger.exception("Failed to stream chat response over websocket")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": str(exc)
                        }
                    )
                )
    except WebSocketDisconnect:
        return


@router.get(
    "/chat/threads/{user_id}",
    response_model=ChatThreadListResponse
)
async def list_threads(
    user_id: str,
    service: ChatService = Depends(get_chat_service)
):
    """Return conversation thread summaries for one user."""

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
    """Return ordered message history for a specific thread."""

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
    """Delete one conversation thread from persisted history."""

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
    """Rename one persisted conversation thread."""

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
import logging
from functools import lru_cache

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from app.schemas.chat import (
    ChatRequest,
    ChatResponse
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
            question=request.question
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )

    except Exception:

        logger.exception("Failed to process chat request")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
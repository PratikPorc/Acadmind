from fastapi import APIRouter

from app.core.llm import check_llm_config
from app.models.schemas import MessageResponse

router = APIRouter()


@router.get("/status", response_model=MessageResponse)
async def llm_status() -> MessageResponse:
    configured, detail = check_llm_config()
    if configured:
        return MessageResponse(message=f"LLM ready: {detail}")
    return MessageResponse(message=f"LLM not configured — {detail}")

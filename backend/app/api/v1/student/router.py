import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import require_student
from app.core.security import AuthUser
from app.models.schemas import (
    BatchDetail,
    BatchResponse,
    FeedItem,
    JarvisUploadResponse,
    PostSummary,
    QueryChatRequest,
    QueryChatResponse,
    UserProfile,
)
from app.services import batch_service, feed_service, post_service
from app.services.query_service import answer_student_query
from app.services.user_service import sync_user_to_graph, to_profile

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def student_me(student: Annotated[AuthUser, Depends(require_student)]) -> UserProfile:
    await sync_user_to_graph(student)
    return to_profile(student)


@router.get("/feed", response_model=list[FeedItem])
async def student_feed(
    student: Annotated[AuthUser, Depends(require_student)],
) -> list[FeedItem]:
    return await feed_service.get_student_feed(student)


@router.get("/batches", response_model=list[BatchResponse])
async def list_batches(
    student: Annotated[AuthUser, Depends(require_student)],
) -> list[BatchResponse]:
    return await batch_service.list_batches_for_user(student)


@router.get("/batches/{batch_id}", response_model=BatchDetail)
async def get_batch(
    batch_id: str,
    student: Annotated[AuthUser, Depends(require_student)],
) -> BatchDetail:
    return await batch_service.get_batch_detail(batch_id, student)


@router.get("/batches/{batch_id}/posts", response_model=list[PostSummary])
async def list_posts(
    batch_id: str,
    student: Annotated[AuthUser, Depends(require_student)],
) -> list[PostSummary]:
    await batch_service.get_batch_detail(batch_id, student)
    return await post_service.list_posts(batch_id)


@router.post("/query/chat", response_model=QueryChatResponse)
async def query_chat(
    payload: QueryChatRequest,
    student: Annotated[AuthUser, Depends(require_student)],
) -> QueryChatResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    answer, sources = await answer_student_query(student, payload.message)
    return QueryChatResponse(
        answer=answer,
        session_id=session_id,
        sources=sources,
    )


@router.post("/jarvis/upload", response_model=JarvisUploadResponse)
async def upload_screenshot(
    student: Annotated[AuthUser, Depends(require_student)],
    file: UploadFile = File(...),
) -> JarvisUploadResponse:
    return JarvisUploadResponse(
        message=(
            f"Jarvis upload ready for {student.full_name or student.email}. "
            f"Received '{file.filename}'. Phase 3 will run OCR and event extraction."
        ),
        extracted_text=None,
        event_id=None,
    )

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status

from app.api.deps import require_faculty
from app.core.security import AuthUser
from app.models.schemas import (
    AddStudentRequest,
    BatchCreate,
    BatchDetail,
    BatchResponse,
    FeedItem,
    PostCreateResponse,
    PostSummary,
    SubjectCreate,
    SubjectResponse,
    UserProfile,
)
from app.services import batch_service, feed_service, post_service
from app.services.user_service import sync_user_to_graph, to_profile

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def faculty_me(faculty: Annotated[AuthUser, Depends(require_faculty)]) -> UserProfile:
    await sync_user_to_graph(faculty)
    return to_profile(faculty)


@router.get("/feed", response_model=list[FeedItem])
async def faculty_feed(
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> list[FeedItem]:
    return await feed_service.get_faculty_feed(faculty)


@router.post("/posts", response_model=PostCreateResponse)
async def create_post_global(
    faculty: Annotated[AuthUser, Depends(require_faculty)],
    batch_id: str = Form(...),
    subject_id: str = Form(...),
    content: str = Form(default=""),
    file: UploadFile | None = File(default=None),
) -> PostCreateResponse:
    file_path: str | None = None
    file_name: str | None = None
    if file and file.filename:
        data = await file.read()
        file_name = file.filename
        file_path = post_service.save_upload(batch_id, file.filename, data)

    if not content.strip() and not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Write a notice or attach a file",
        )

    return await post_service.create_post(
        batch_id=batch_id,
        subject_id=subject_id,
        faculty=faculty,
        content=content.strip(),
        file_name=file_name,
        file_path=file_path,
    )


@router.post("/batches", response_model=BatchResponse)
async def create_batch(
    payload: BatchCreate,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> BatchResponse:
    return await batch_service.create_batch(faculty, payload)


@router.get("/batches", response_model=list[BatchResponse])
async def list_batches(
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> list[BatchResponse]:
    return await batch_service.list_batches_for_user(faculty)


@router.get("/batches/{batch_id}", response_model=BatchDetail)
async def get_batch(
    batch_id: str,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> BatchDetail:
    return await batch_service.get_batch_detail(batch_id, faculty)


@router.post("/batches/{batch_id}/subjects", response_model=SubjectResponse)
async def add_subject(
    batch_id: str,
    payload: SubjectCreate,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> SubjectResponse:
    return await batch_service.add_subject(batch_id, faculty, payload)


@router.post("/batches/{batch_id}/students")
async def add_student(
    batch_id: str,
    payload: AddStudentRequest,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> dict[str, str]:
    return await batch_service.add_student_to_batch(batch_id, faculty, payload.enrollment_id)


@router.delete("/batches/{batch_id}/students/{enrollment_id}")
async def remove_student(
    batch_id: str,
    enrollment_id: str,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> dict[str, str]:
    return await batch_service.remove_student_from_batch(batch_id, faculty, enrollment_id)


@router.get("/batches/{batch_id}/posts", response_model=list[PostSummary])
async def list_posts(
    batch_id: str,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
) -> list[PostSummary]:
    await batch_service.get_batch_detail(batch_id, faculty)
    return await post_service.list_posts(batch_id)


@router.post("/batches/{batch_id}/posts", response_model=PostCreateResponse)
async def create_post_in_batch(
    batch_id: str,
    faculty: Annotated[AuthUser, Depends(require_faculty)],
    subject_id: str = Form(...),
    content: str = Form(default=""),
    file: UploadFile | None = File(default=None),
) -> PostCreateResponse:
    file_path: str | None = None
    file_name: str | None = None
    if file and file.filename:
        data = await file.read()
        file_name = file.filename
        file_path = post_service.save_upload(batch_id, file.filename, data)

    if not content.strip() and not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Write a notice or attach a file",
        )

    return await post_service.create_post(
        batch_id=batch_id,
        subject_id=subject_id,
        faculty=faculty,
        content=content.strip(),
        file_name=file_name,
        file_path=file_path,
    )

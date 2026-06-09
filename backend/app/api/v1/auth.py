from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.security import AuthUser
from app.db.supabase import check_supabase_config, get_supabase_admin
from app.config import get_settings
from app.models.schemas import MessageResponse, SignUpRequest, UserProfile, UserProfileUpdate, UserRole
from app.services.user_service import sync_user_to_graph, to_profile

router = APIRouter()


@router.get("/status", response_model=MessageResponse)
async def auth_status() -> MessageResponse:
    configured, detail = check_supabase_config()
    if configured:
        return MessageResponse(message=f"Supabase auth ready ({detail})")
    return MessageResponse(
        message="Supabase not configured. Copy backend/.env.example to backend/.env and add keys."
    )


@router.post("/signup", response_model=MessageResponse)
async def signup(payload: SignUpRequest) -> MessageResponse:
    settings = get_settings()
    if not settings.auth_auto_confirm_signup:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Direct signup disabled. Use email confirmation flow.",
        )

    if payload.role == UserRole.student and not (payload.enrollment_id or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID is required",
        )

    admin = get_supabase_admin()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase admin client not configured",
        )

    enrollment_id = payload.enrollment_id
    metadata = {
        "role": payload.role.value,
        "full_name": payload.full_name,
        "enrollment_id": enrollment_id,
        "semester": payload.semester,
        "branch": payload.branch,
    }

    try:
        response = admin.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": metadata,
            }
        )
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        if "already been registered" in message or "already exists" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create account: {message}",
        ) from exc

    user_id = response.user.id if response and response.user else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Account created but user id missing",
        )

    user = AuthUser(
        id=user_id,
        email=payload.email,
        role=payload.role,
        full_name=payload.full_name,
        semester=payload.semester,
        branch=payload.branch,
        enrollment_id=enrollment_id,
    )
    await sync_user_to_graph(user)
    return MessageResponse(message="Account created")


@router.get("/me", response_model=UserProfile)
async def get_me(user: Annotated[AuthUser, Depends(get_current_user)]) -> UserProfile:
    await sync_user_to_graph(user)
    return to_profile(user)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    payload: UserProfileUpdate,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> UserProfile:
    admin = get_supabase_admin()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase admin client not configured",
        )

    metadata = {
        "role": user.role.value,
        "full_name": payload.full_name if payload.full_name is not None else user.full_name,
        "semester": payload.semester if payload.semester is not None else user.semester,
        "branch": payload.branch if payload.branch is not None else user.branch,
    }

    try:
        admin.auth.admin.update_user_by_id(user.id, {"user_metadata": metadata})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to update profile: {exc}",
        ) from exc

    updated = AuthUser(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=metadata["full_name"],
        semester=metadata["semester"],
        branch=metadata["branch"],
    )
    await sync_user_to_graph(updated)
    return to_profile(updated)

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.utils.enrollment import normalize_enrollment_id


class UserRole(str, Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class HealthStatus(str, Enum):
    ok = "ok"
    degraded = "degraded"
    error = "error"


class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    detail: str | None = None


class HealthResponse(BaseModel):
    status: HealthStatus
    app: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    services: list[ServiceHealth]


class MessageResponse(BaseModel):
    message: str


class GatewayLogEntrySchema(BaseModel):
    request_id: str
    method: str
    path: str
    query: str
    status_code: int
    duration_ms: float
    client_ip: str
    user_email: str | None = None
    user_role: str | None = None
    error: str | None = None
    timestamp: str


class GatewayLogResponse(BaseModel):
    count: int
    entries: list[GatewayLogEntrySchema]


class UserProfile(BaseModel):
    id: str
    email: str
    role: UserRole
    full_name: str | None = None
    semester: str | None = None
    branch: str | None = None
    enrollment_id: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    semester: str | None = None
    branch: str | None = None


class SignUpRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)
    role: UserRole
    enrollment_id: str | None = None
    semester: str | None = None
    branch: str | None = None

    @field_validator("enrollment_id")
    @classmethod
    def validate_enrollment_id(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return value
        return normalize_enrollment_id(value)


class QueryChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class QueryChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    phase: str = "Knowledge Graph + RAG"


class EventCategory(str, Enum):
    academic = "academic"
    cultural = "cultural"
    technical = "technical"
    global_ = "global"


class StudentSubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    batch_id: str
    batch_code: str | None = None


class CampusGroupResponse(BaseModel):
    name: str


class CampusOptionsResponse(BaseModel):
    clubs: list[str]
    domains: list[str]
    global_scopes: list[str]


class BatchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: str = Field(..., min_length=1, max_length=32)
    semester: str = Field(default="", max_length=16)
    branch: str = Field(default="", max_length=32)


class BatchResponse(BaseModel):
    id: str
    name: str
    code: str
    semester: str
    branch: str
    student_count: int = 0
    subject_count: int = 0


class BatchDetail(BatchResponse):
    subjects: list["SubjectResponse"] = Field(default_factory=list)
    student_enrollment_ids: list[str] = Field(default_factory=list)


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: str = Field(..., min_length=1, max_length=16)


class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    batch_id: str


class AddStudentRequest(BaseModel):
    enrollment_id: str = Field(
        ...,
        min_length=12,
        max_length=12,
        description="Full 12-digit institutional student ID e.g. 231003003137",
    )

    @field_validator("enrollment_id")
    @classmethod
    def validate_enrollment_id(cls, value: str) -> str:
        return normalize_enrollment_id(value)


class PostCreateResponse(BaseModel):
    post_id: str
    message: str
    parsed: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None
    resource_id: str | None = None


class PostSummary(BaseModel):
    id: str
    content: str
    post_type: str
    event_category: str = "academic"
    global_scope: str | None = None
    group_name: str | None = None
    subject_name: str | None = None
    subject_code: str | None = None
    batch_code: str | None = None
    batch_name: str | None = None
    due_date: str | None = None
    created_at: str | None = None


class FeedItem(BaseModel):
    id: str
    title: str
    content: str
    item_type: str
    event_category: str = "academic"
    global_scope: str | None = None
    group_name: str | None = None
    subject_code: str | None = None
    batch_code: str | None = None
    due_date: str | None = None
    created_at: str | None = None


class QuerySource(BaseModel):
    type: str
    title: str
    subject: str | None = None
    batch: str | None = None
    due_date: str | None = None

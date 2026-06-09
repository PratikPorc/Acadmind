import logging
from dataclasses import dataclass
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings
from app.db.supabase import get_supabase_admin
from app.models.schemas import UserRole

logger = logging.getLogger(__name__)


@dataclass
class AuthUser:
    id: str
    email: str
    role: UserRole
    full_name: str | None = None
    semester: str | None = None
    branch: str | None = None
    enrollment_id: str | None = None

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> "AuthUser":
        metadata = claims.get("user_metadata") or {}
        return cls.from_metadata(
            user_id=claims["sub"],
            email=claims.get("email", ""),
            metadata=metadata,
        )

    @classmethod
    def from_metadata(
        cls,
        user_id: str,
        email: str,
        metadata: dict[str, Any],
    ) -> "AuthUser":
        role_raw = metadata.get("role", UserRole.student.value)
        try:
            role = UserRole(role_raw)
        except ValueError:
            role = UserRole.student

        return cls(
            id=user_id,
            email=email,
            role=role,
            full_name=metadata.get("full_name"),
            semester=metadata.get("semester"),
            branch=metadata.get("branch"),
            enrollment_id=metadata.get("enrollment_id") or metadata.get("student_id"),
        )


def _decode_with_jwt_secret(token: str) -> AuthUser | None:
    settings = get_settings()
    if not settings.supabase_jwt_secret:
        return None

    decode_attempts = [
        {"algorithms": ["HS256"], "audience": "authenticated"},
        {"algorithms": ["HS256"], "options": {"verify_aud": False}},
    ]

    for kwargs in decode_attempts:
        try:
            claims = jwt.decode(token, settings.supabase_jwt_secret, **kwargs)
            return AuthUser.from_claims(claims)
        except JWTError:
            continue

    return None


def _decode_with_supabase_api(token: str) -> AuthUser | None:
    admin = get_supabase_admin()
    if admin is None:
        return None

    try:
        response = admin.auth.get_user(token)
        if not response or not response.user:
            return None

        user = response.user
        metadata = user.user_metadata or {}
        return AuthUser.from_metadata(
            user_id=user.id,
            email=user.email or "",
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Supabase get_user failed: %s", exc)
        return None


def decode_supabase_jwt(token: str) -> AuthUser | None:
    # Prefer Supabase API — works with legacy HS256 and new asymmetric JWT keys.
    user = _decode_with_supabase_api(token)
    if user is not None:
        return user

    user = _decode_with_jwt_secret(token)
    if user is not None:
        return user

    logger.warning("Failed to validate Supabase access token")
    return None

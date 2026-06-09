from app.core.security import AuthUser

STUDENT_MATCH = """
MATCH (s:Student)
WHERE s.id = $uid OR ($enrollment_id <> '' AND s.enrollment_id = $enrollment_id)
"""


def student_params(user: AuthUser) -> dict[str, str]:
    return {
        "uid": user.id,
        "enrollment_id": (user.enrollment_id or "").strip(),
    }

import re

ENROLLMENT_ID_RE = re.compile(r"^\d{12}$")


def normalize_enrollment_id(value: str) -> str:
    """Validate and normalize institutional student ID (12 digits)."""
    normalized = value.strip()
    if not ENROLLMENT_ID_RE.match(normalized):
        raise ValueError("Student ID must be exactly 12 digits (e.g. 231003003137)")
    return normalized

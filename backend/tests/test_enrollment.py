import pytest

from app.utils.enrollment import normalize_enrollment_id


def test_normalize_enrollment_id_accepts_twelve_digits():
    assert normalize_enrollment_id("231003003137") == "231003003137"
    assert normalize_enrollment_id("  231003003137  ") == "231003003137"


@pytest.mark.parametrize(
    "value",
    ["123", "2310030031371", "abc231003003137", ""],
)
def test_normalize_enrollment_id_rejects_invalid(value):
    with pytest.raises(ValueError, match="12 digits"):
        normalize_enrollment_id(value)

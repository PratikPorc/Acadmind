from app.services.query_service import _context_entries, _score_entry, _tokenize


def test_tokenize_strips_stop_words():
    tokens = _tokenize("When is the CN exam?")
    assert "cn" in tokens
    assert "exam" in tokens
    assert "when" not in tokens


def test_score_entry_matches_subject_code():
    entry = {
        "title": "CN Mid-Term Examination",
        "content": "Computer Networks exam on 15 July",
        "category": "academic",
        "global_scope": "",
        "group_name": "",
        "subject": "CN",
        "batch": "CSE6A",
        "due_date": "2026-07-15",
        "haystack": "cn mid-term examination computer networks exam cse6a",
    }
    score = _score_entry(entry, _tokenize("CN exam date"))
    assert score > 0


def test_score_entry_matches_hackathon():
    entry = {
        "title": "AI & ML Hackathon 2026",
        "content": "48-hour hackathon in July",
        "category": "technical",
        "global_scope": "",
        "group_name": "AI & Machine Learning",
        "subject": "",
        "batch": "CSE6A",
        "due_date": "2026-07-11",
        "haystack": "ai ml hackathon 2026 technical",
    }
    score = _score_entry(entry, _tokenize("any hackathons this month"))
    assert score > 0


def test_context_entries_deduplicates():
    rows = [
        {
            "post_title": "CN Exam",
            "post_content": "Exam soon",
            "post_category": "academic",
            "subject_code": "CN",
            "batch_code": "CSE6A",
        },
        {
            "post_title": "CN Exam",
            "post_content": "Exam soon",
            "post_category": "academic",
            "subject_code": "CN",
            "batch_code": "CSE6A",
        },
    ]
    assert len(_context_entries(rows)) == 1

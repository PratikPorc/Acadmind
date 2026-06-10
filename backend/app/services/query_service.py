import re
from typing import Any

from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.services.demo_seed_service import ensure_demo_enrollment
from app.utils.student_graph import STUDENT_MATCH, student_params

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "what",
        "when",
        "where",
        "who",
        "how",
        "why",
        "which",
        "any",
        "there",
        "this",
        "that",
        "for",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "at",
        "my",
        "me",
        "about",
        "tell",
        "jarvis",
        "please",
        "can",
        "you",
        "do",
        "does",
        "due",
        "date",
    }
)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "academic": ("exam", "assignment", "subject", "mid", "term", "lab", "cn", "se", "ds", "syllabus"),
    "cultural": ("fest", "dance", "music", "club", "cultural", "open", "mic", "audition"),
    "technical": ("hackathon", "workshop", "tech", "web", "development", "ai", "ml", "coding"),
    "global": ("break", "holiday", "registration", "summit", "campus", "spring"),
}


async def fetch_student_context(user: AuthUser) -> list[dict[str, Any]]:
    """Load one row per campus post (no cross-join with subjects/events)."""
    await ensure_demo_enrollment(user.id, user.enrollment_id)

    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub:Subject)
            RETURN DISTINCT
                p.id AS post_id,
                b.name AS batch_name,
                b.code AS batch_code,
                sub.code AS subject_code,
                sub.name AS subject_name,
                p.title AS post_title,
                p.content AS post_content,
                p.summary AS post_summary,
                p.search_text AS search_text,
                p.post_type AS post_type,
                p.event_category AS post_category,
                p.global_scope AS global_scope,
                p.group_name AS group_name,
                p.due_date AS post_due_date
            ORDER BY post_due_date, batch_code, subject_code
            """,
            **student_params(user),
        )
        return await result.data()


def _stem(word: str) -> str:
    w = word.lower()
    if len(w) > 3 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s"):
        return w[:-1]
    return w


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    result: set[str] = set()
    for w in words:
        if w in STOP_WORDS:
            continue
        if len(w) >= 2:
            result.add(w)
            result.add(_stem(w))
    return result


def _question_intents(question: str) -> set[str]:
    """Map question text to campus categories (handles plurals / partial words)."""
    q = question.lower()
    intents: set[str] = set()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in q or _stem(kw) in q:
                intents.add(cat)
                break
    return intents


def _tokens_relate(query_token: str, hay_token: str) -> bool:
    if query_token == hay_token:
        return True
    qs, hs = _stem(query_token), _stem(hay_token)
    if qs == hs:
        return True
    if len(qs) >= 4 and (qs in hay_token or hay_token in qs):
        return True
    if len(hs) >= 4 and (hs in query_token or query_token in hs):
        return True
    return False


def _entry_key(row: dict[str, Any]) -> str:
    post_id = row.get("post_id")
    if post_id:
        return str(post_id)
    title = row.get("post_title") or row.get("post_content") or ""
    return f"{title}|{row.get('post_due_date')}|{row.get('post_category')}"


def _context_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in rows:
        title = row.get("post_title")
        content = row.get("post_content") or ""
        summary = row.get("post_summary") or ""
        search_text = row.get("search_text") or ""
        if not title and not content:
            continue

        key = _entry_key(row)
        if key in seen:
            continue
        seen.add(key)

        category = row.get("post_category") or "academic"
        subject_code = row.get("subject_code") or ""
        group_name = row.get("group_name") or ""

        entries.append(
            {
                "post_id": row.get("post_id"),
                "title": title or content[:80],
                "content": content,
                "type": row.get("post_type") or "notice",
                "category": category,
                "global_scope": row.get("global_scope") or "",
                "group_name": group_name,
                "subject": subject_code or row.get("subject_name") or "",
                "batch": row.get("batch_code") or "",
                "due_date": row.get("post_due_date") or "",
                "haystack": search_text
                or " ".join(
                    filter(
                        None,
                        [
                            title,
                            summary,
                            content,
                            category,
                            row.get("global_scope"),
                            group_name,
                            subject_code,
                            row.get("subject_name"),
                            row.get("batch_code"),
                        ],
                    )
                ).lower(),
            }
        )
    return entries


def _score_entry(entry: dict[str, Any], question: str, question_tokens: set[str]) -> float:
    if not question_tokens:
        return 0.0

    haystack = entry["haystack"]
    haystack_tokens = _tokenize(haystack)
    score = 0.0

    for q in question_tokens:
        if q in STOP_WORDS or len(q) < 2:
            continue
        if q in haystack_tokens:
            score += 2.0
        elif q in haystack:
            score += 1.5
        else:
            for h in haystack_tokens:
                if _tokens_relate(q, h):
                    score += 1.5
                    break

    category = entry["category"]
    scope = entry.get("global_scope") or ""
    intents = _question_intents(question)
    if category in intents:
        score += 3.0
    elif category == "global" and scope in intents:
        score += 2.5

    return score


def _format_answer(match: dict[str, Any]) -> str:
    parts = [match["title"]]
    if match["category"]:
        label = match["category"]
        if match.get("global_scope"):
            label = f"global · {match['global_scope']}"
        parts.append(f"({label})")
    if match["subject"]:
        parts.append(f"— {match['subject']}")
    if match["group_name"]:
        parts.append(f"· {match['group_name']}")
    if match["due_date"]:
        parts.append(f"· due {match['due_date']}")
    line = " ".join(parts)
    if match["content"] and match["content"] != match["title"]:
        return f"{line}\n\n{match['content']}"
    return line


def _best_match(scored: list[tuple[dict[str, Any], float]], min_score: float = 1.5) -> dict[str, Any] | None:
    for entry, score in scored:
        if score >= min_score:
            return entry
    return None


async def answer_student_query(user: AuthUser, question: str) -> tuple[str, list[dict[str, Any]]]:
    context_rows = await fetch_student_context(user)

    if not context_rows:
        student_hint = user.enrollment_id or "your 12-digit Student ID"
        return (
            f"You are not enrolled in any batch yet. Ask your faculty to add your full "
            f"Student ID ({student_hint}) to a batch.",
            [],
        )

    entries = _context_entries(context_rows)
    question_tokens = _tokenize(question)

    if not question_tokens:
        return (
            "Ask about exams, assignments, cultural fests, hackathons, or campus updates — "
            "e.g. “When is the CN exam?” or “Any hackathons?”",
            [],
        )

    scored = sorted(
        ((entry, _score_entry(entry, question, question_tokens)) for entry in entries),
        key=lambda x: x[1],
        reverse=True,
    )
    best = _best_match(scored)

    if not best:
        return (
            "I couldn't find a matching notice in your campus feed. Try keywords like "
            "CN, exam, hackathon, dance, fest, or break.",
            [],
        )

    sources = [
        {
            "type": best["type"],
            "category": best["category"] if not best.get("global_scope") else f"global/{best['global_scope']}",
            "title": best["title"],
            "subject": best["subject"],
            "batch": best["batch"],
            "due_date": best["due_date"],
        }
    ]

    answer = _format_answer(best)
    return answer, sources

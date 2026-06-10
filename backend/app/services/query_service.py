from typing import Any

from app.core.llm import get_chat_model
from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.utils.student_graph import STUDENT_MATCH, student_params


async def fetch_student_context(user: AuthUser) -> list[dict[str, Any]]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            OPTIONAL MATCH (e:Event)-[:IN_BATCH]->(b)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(sub)
            OPTIONAL MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub2:Subject)
            RETURN DISTINCT
                b.name AS batch_name,
                b.code AS batch_code,
                sub.code AS subject_code,
                sub.name AS subject_name,
                e.title AS event_title,
                e.event_type AS event_type,
                e.event_category AS event_category,
                e.due_date AS due_date,
                e.summary AS event_summary,
                p.content AS post_content,
                p.title AS post_title,
                p.post_type AS post_type,
                p.event_category AS post_category,
                p.due_date AS post_due_date
            ORDER BY due_date, batch_code, subject_code
            """,
            **student_params(user),
        )
        return await result.data()


async def answer_student_query(user: AuthUser, question: str) -> tuple[str, list[dict[str, Any]]]:
    context_rows = await fetch_student_context(user)

    if not context_rows:
        student_hint = user.enrollment_id or "your 12-digit Student ID"
        return (
            f"You are not enrolled in any batch yet. Ask your faculty to add your full "
            f"Student ID ({student_hint}) to a batch.",
            [],
        )

    context_text = _format_context(context_rows)
    sources = _build_sources(context_rows, question)

    prompt = f"""You are Jarvis, AcadMind's campus knowledge assistant for Techno India University students.
Answer using ONLY the context below from the Neo4j knowledge graph (faculty notices seeded as posts and events).
Group your understanding across academic, cultural, and technical campus events when relevant.
If the answer is not in the context, say so clearly.
Include specific dates, subjects, event categories, and batch names when relevant. Be concise.

CONTEXT:
{context_text}

STUDENT QUESTION: {question}

ANSWER:"""

    llm = get_chat_model()
    response = llm.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    return answer, sources


def _format_context(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for row in rows:
        batch = f"{row.get('batch_name')} ({row.get('batch_code')})"
        subj = row.get("subject_code") or row.get("subject_name") or "General"
        category = row.get("event_category") or row.get("post_category") or "academic"
        key = f"{batch}|{subj}|{category}|{row.get('event_title')}|{row.get('post_title')}"
        if key in seen:
            continue
        seen.add(key)

        parts = [f"Batch: {batch}", f"Category: {category}", f"Subject: {subj}"]
        if row.get("event_title"):
            parts.append(
                f"Event [{row.get('event_type')}]: {row['event_title']} "
                f"due {row.get('due_date') or 'TBD'} — {row.get('event_summary') or ''}"
            )
        if row.get("post_title") or row.get("post_content"):
            parts.append(
                f"Notice [{row.get('post_type')}]: {row.get('post_title') or ''} "
                f"{row.get('post_content') or ''} (due: {row.get('post_due_date') or 'n/a'})"
            )
        lines.append(" | ".join(parts))
    return "\n".join(lines) if lines else "No notices seeded yet."


def _build_sources(rows: list[dict[str, Any]], question: str) -> list[dict[str, Any]]:
    q = question.lower()
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in rows:
        title = row.get("event_title") or row.get("post_title")
        if not title:
            continue
        subj = row.get("subject_code") or row.get("subject_name") or ""
        category = row.get("event_category") or row.get("post_category") or "academic"
        haystack = f"{title} {subj} {category} {row.get('post_content', '')}".lower()
        if not any(word in haystack for word in q.split() if len(word) > 3):
            if row.get("due_date") or row.get("post_due_date"):
                pass
            elif not any(k in q for k in ("deadline", "exam", "assignment", "cultural", "technical", "fest", "hackathon")):
                continue

        key = f"{title}|{subj}|{category}"
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "type": row.get("event_type") or row.get("post_type") or "notice",
                "category": category,
                "title": title,
                "subject": subj,
                "batch": row.get("batch_code"),
                "due_date": row.get("due_date") or row.get("post_due_date"),
            }
        )
    return sources[:5]

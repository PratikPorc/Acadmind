import logging
import re
import uuid
from difflib import get_close_matches
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.llm import get_chat_model
from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import PostCreateResponse, PostSummary, SubjectResponse
from app.services.batch_service import get_batch_subjects, _assert_faculty_owns_batch

logger = logging.getLogger(__name__)


class ParsedNotice(BaseModel):
    subject_code: str | None = Field(
        default=None,
        description="Subject code like CN, SE, DS — match batch subjects",
    )
    subject_name: str | None = Field(default=None, description="Full subject name if mentioned")
    post_type: str = Field(
        description="One of: exam, assignment, notice, resource",
    )
    title: str = Field(description="Short title for the notice or event")
    due_date: str | None = Field(
        default=None,
        description="ISO date YYYY-MM-DD if a deadline or exam date is mentioned",
    )
    summary: str = Field(description="One sentence summary of the notice")


def _match_subject(
    parsed: ParsedNotice,
    subjects: list[SubjectResponse],
) -> SubjectResponse | None:
    if not subjects:
        return None

    code_map = {s.code.upper(): s for s in subjects}
    name_map = {s.name.lower(): s for s in subjects}

    if parsed.subject_code:
        code = parsed.subject_code.upper().strip()
        if code in code_map:
            return code_map[code]
        for sub in subjects:
            if sub.code.upper().startswith(code) or code.startswith(sub.code.upper()):
                return sub

    if parsed.subject_name:
        name_lower = parsed.subject_name.lower()
        if name_lower in name_map:
            return name_map[name_lower]
        aliases = {
            "cn": "computer networks",
            "se": "software engineering",
            "ds": "data structures",
            "os": "operating systems",
            "dbms": "database",
        }
        for alias, full in aliases.items():
            if alias in name_lower or full in name_lower:
                for sub in subjects:
                    if alias in sub.code.lower() or full in sub.name.lower():
                        return sub
        close = get_close_matches(name_lower, list(name_map.keys()), n=1, cutoff=0.6)
        if close:
            return name_map[close[0]]

    # Try matching from title/summary text
    haystack = f"{parsed.title} {parsed.summary}".lower()
    for sub in subjects:
        if sub.code.lower() in haystack or sub.name.lower() in haystack:
            return sub

    return subjects[0] if len(subjects) == 1 else None


async def parse_notice(
    content: str,
    batch_name: str,
    batch_code: str,
    subjects: list[SubjectResponse],
) -> ParsedNotice:
    subject_list = ", ".join(f"{s.code} ({s.name})" for s in subjects) or "none yet"

    prompt = f"""Parse this academic notice for batch "{batch_name}" ({batch_code}).

Available subjects in this batch: {subject_list}

Notice text:
\"\"\"
{content}
\"\"\"

Rules:
- Match subject by code or name (CN = Computer Networks, SE = Software Engineering, etc.)
- post_type: exam | assignment | notice | resource
- Extract due_date as YYYY-MM-DD when a date is mentioned (e.g. 15th July 2026 → 2026-07-15)
- If only a document/resource is mentioned with no deadline, use post_type=resource
"""

    llm = get_chat_model()
    structured = llm.with_structured_output(ParsedNotice)
    try:
        return structured.invoke(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Structured parse failed, using fallback: %s", exc)
        return ParsedNotice(
            post_type="notice",
            title=content[:80],
            summary=content,
        )


async def create_post(
    batch_id: str,
    subject_id: str,
    faculty: AuthUser,
    content: str,
    file_name: str | None = None,
    file_path: str | None = None,
) -> PostCreateResponse:
    await _assert_faculty_owns_batch(batch_id, faculty.id)
    subjects = await get_batch_subjects(batch_id)
    subject = next((s for s in subjects if s.id == subject_id), None)
    if not subject:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subject for batch")

    driver = get_neo4j_driver()
    async with driver.session() as session:
        batch_result = await session.run(
            "MATCH (b:Batch {id: $id}) RETURN b.name AS name, b.code AS code",
            id=batch_id,
        )
        batch_record = await batch_result.single()
        if not batch_record:
            raise ValueError("Batch not found")

    parsed = await parse_notice(
        content=content or (file_name or "Uploaded resource"),
        batch_name=batch_record["name"],
        batch_code=batch_record["code"],
        subjects=[subject],
    )

    post_id = str(uuid.uuid4())
    event_id: str | None = None
    resource_id: str | None = None
    post_type = parsed.post_type.lower()
    if file_path and post_type not in ("exam", "assignment"):
        post_type = "resource"

    async with driver.session() as session:
        await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            MATCH (f:Faculty {id: $faculty_id})
            CREATE (p:Post {
                id: $post_id,
                content: $content,
                post_type: $post_type,
                file_name: $file_name,
                file_path: $file_path,
                title: $title,
                due_date: $due_date,
                created_at: datetime()
            })
            MERGE (p)-[:FOR_BATCH]->(b)
            MERGE (p)-[:CREATED_BY]->(f)
            """,
            batch_id=batch_id,
            faculty_id=faculty.id,
            post_id=post_id,
            content=content,
            post_type=post_type,
            file_name=file_name or "",
            file_path=file_path or "",
            title=parsed.title,
            due_date=parsed.due_date or "",
        )

        if subject:
            await session.run(
                """
                MATCH (p:Post {id: $post_id}), (sub:Subject {id: $subject_id})
                MERGE (p)-[:FOR_SUBJECT]->(sub)
                """,
                post_id=post_id,
                subject_id=subject.id,
            )

        if post_type in ("exam", "assignment") or parsed.due_date:
            event_id = str(uuid.uuid4())
            await session.run(
                """
                MATCH (p:Post {id: $post_id}), (b:Batch {id: $batch_id})
                CREATE (e:Event {
                    id: $event_id,
                    title: $title,
                    event_type: $event_type,
                    due_date: $due_date,
                    summary: $summary,
                    created_at: datetime()
                })
                MERGE (e)-[:FROM_POST]->(p)
                MERGE (e)-[:IN_BATCH]->(b)
                WITH e, p
                OPTIONAL MATCH (sub:Subject {id: $subject_id})
                FOREACH (_ IN CASE WHEN sub IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (e)-[:BELONGS_TO]->(sub)
                )
                """,
                post_id=post_id,
                batch_id=batch_id,
                event_id=event_id,
                title=parsed.title,
                event_type=post_type if post_type in ("exam", "assignment") else "deadline",
                due_date=parsed.due_date or "",
                summary=parsed.summary,
                subject_id=subject.id if subject else "",
            )

        if file_path or post_type == "resource":
            resource_id = str(uuid.uuid4())
            await session.run(
                """
                MATCH (p:Post {id: $post_id}), (b:Batch {id: $batch_id})
                CREATE (r:Resource {
                    id: $resource_id,
                    title: $title,
                    file_name: $file_name,
                    file_path: $file_path,
                    created_at: datetime()
                })
                MERGE (r)-[:FROM_POST]->(p)
                MERGE (r)-[:FOR_BATCH]->(b)
                WITH r
                OPTIONAL MATCH (sub:Subject {id: $subject_id})
                FOREACH (_ IN CASE WHEN sub IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (r)-[:FOR_SUBJECT]->(sub)
                )
                """,
                post_id=post_id,
                batch_id=batch_id,
                resource_id=resource_id,
                title=parsed.title or file_name or "Resource",
                file_name=file_name or "",
                file_path=file_path or "",
                subject_id=subject.id if subject else "",
            )

    parsed_dict = parsed.model_dump()
    parsed_dict["matched_subject"] = {"code": subject.code, "name": subject.name}

    return PostCreateResponse(
        post_id=post_id,
        message=f"Post created and graph seeded ({post_type})",
        parsed=parsed_dict,
        event_id=event_id,
        resource_id=resource_id,
    )


async def list_posts(batch_id: str) -> list[PostSummary]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Post)-[:FOR_BATCH]->(b:Batch {id: $batch_id})
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub:Subject)
            RETURN p, b.code AS batch_code, b.name AS batch_name,
                   sub.code AS subject_code, sub.name AS subject_name
            ORDER BY p.created_at DESC
            """,
            batch_id=batch_id,
        )
        records = await result.data()

    posts: list[PostSummary] = []
    for r in records:
        p = r["p"]
        created = p.get("created_at")
        created_str = str(created) if created else None
        posts.append(
            PostSummary(
                id=p["id"],
                content=p.get("content", ""),
                post_type=p.get("post_type", "notice"),
                subject_name=r.get("subject_name"),
                subject_code=r.get("subject_code"),
                batch_code=r.get("batch_code"),
                batch_name=r.get("batch_name"),
                due_date=p.get("due_date") or None,
                file_name=p.get("file_name") or None,
                created_at=created_str,
            )
        )
    return posts


def save_upload(batch_id: str, filename: str, data: bytes) -> str:
    settings = get_settings()
    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    dest_dir = Path(settings.upload_dir) / "posts" / batch_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4().hex}_{safe_name}"
    dest.write_bytes(data)
    return str(dest)

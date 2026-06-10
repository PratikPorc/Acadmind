import logging
from difflib import get_close_matches

from pydantic import BaseModel, Field

from app.constants.campus import CAMPUS_CLUBS, CAMPUS_DOMAINS, GLOBAL_SCOPES
from app.core.llm import get_chat_model
from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import PostCreateResponse, PostSummary, SubjectResponse
from app.services.batch_service import get_batch_subjects, _assert_faculty_owns_batch
from app.services.knowledge_graph_service import NoticeGraphPayload, ingest_faculty_notice

logger = logging.getLogger(__name__)

VALID_EVENT_CATEGORIES = frozenset({"academic", "cultural", "technical", "global"})


class ParsedNotice(BaseModel):
    subject_code: str | None = Field(
        default=None,
        description="Subject code like CN, SE, DS — match batch subjects",
    )
    subject_name: str | None = Field(default=None, description="Full subject name if mentioned")
    post_type: str = Field(
        description="One of: exam, assignment, notice, resource",
    )
    event_category: str = Field(
        description="One of: academic, cultural, technical, global",
    )
    group_name: str | None = Field(
        default=None,
        description="Club name for cultural or domain name for technical notices",
    )
    title: str = Field(description="Short title for the notice or event")
    due_date: str | None = Field(
        default=None,
        description="ISO date YYYY-MM-DD if a deadline or exam date is mentioned",
    )
    summary: str = Field(description="One sentence summary of the notice")


def _normalize_event_category(value: str) -> str:
    normalized = value.lower().strip()
    return normalized if normalized in VALID_EVENT_CATEGORIES else "academic"


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
    event_category: str = "academic",
    group_name: str | None = None,
) -> ParsedNotice:
    subject_list = ", ".join(f"{s.code} ({s.name})" for s in subjects) or "none yet"
    category = _normalize_event_category(event_category)

    prompt = f"""Parse this campus notice for batch "{batch_name}" ({batch_code}).

Available subjects in this batch: {subject_list}
Faculty-selected category: {category}
Faculty-selected group (club/domain): {group_name or "infer from notice"}

Notice text:
\"\"\"
{content}
\"\"\"

Rules:
- event_category: academic | cultural | technical | global
  - academic: exams, assignments, subject notices, syllabus, resources
  - cultural: fests, cultural events, dance, music, celebrations, sports meets
  - technical: hackathons, tech fests, workshops, seminars, coding competitions, tech talks
  - global: campus-wide updates, holidays, admin notices, general announcements
- group_name: club name (cultural) or domain name (technical), e.g. "Dance Club", "AI & ML"
- Match subject by code or name when the notice is academic (CN = Computer Networks, etc.)
- post_type: exam | assignment | notice | resource
- Extract due_date as YYYY-MM-DD when a date is mentioned (e.g. 15th July 2026 → 2026-07-15)
"""

    llm = get_chat_model()
    structured = llm.with_structured_output(ParsedNotice)
    try:
        parsed = structured.invoke(prompt)
        parsed.event_category = _normalize_event_category(parsed.event_category or category)
        if group_name and not parsed.group_name:
            parsed.group_name = group_name.strip()
        return parsed
    except Exception as exc:  # noqa: BLE001
        logger.warning("Structured parse failed, using fallback: %s", exc)
        return ParsedNotice(
            post_type="notice",
            event_category=category,
            title=content[:80],
            summary=content,
        )


def _validate_post_fields(
    category: str,
    group_name: str | None,
    global_scope: str | None,
) -> tuple[str | None, str | None]:
    from fastapi import HTTPException, status

    scope: str | None = None
    group: str | None = None

    if category == "academic":
        return None, None
    if category == "cultural":
        if not group_name or group_name not in CAMPUS_CLUBS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select a valid club from the list",
            )
        return None, group_name
    if category == "technical":
        if not group_name or group_name not in CAMPUS_DOMAINS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select a valid domain from the list",
            )
        return None, group_name
    if category == "global":
        if not global_scope or global_scope not in GLOBAL_SCOPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select global scope: academic, cultural, or technical",
            )
        return global_scope, None
    return scope, group


async def create_post(
    batch_id: str,
    subject_id: str | None,
    faculty: AuthUser,
    content: str,
    event_category: str = "academic",
    group_name: str | None = None,
    global_scope: str | None = None,
) -> PostCreateResponse:
    await _assert_faculty_owns_batch(batch_id, faculty.id)
    category = _normalize_event_category(event_category)
    validated_scope, validated_group = _validate_post_fields(category, group_name, global_scope)
    group_name = validated_group
    global_scope = validated_scope
    subjects = await get_batch_subjects(batch_id)

    subject: SubjectResponse | None = None
    if subject_id:
        subject = next((s for s in subjects if s.id == subject_id), None)
        if not subject:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subject for batch")
    elif category == "academic":
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is required for academic notices",
        )

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
        content=content,
        batch_name=batch_record["name"],
        batch_code=batch_record["code"],
        subjects=subjects if subjects else ([subject] if subject else []),
        event_category=category,
        group_name=group_name,
    )
    parsed.event_category = category
    if group_name:
        parsed.group_name = group_name.strip()

    if category == "academic" and not subject:
        subject = _match_subject(parsed, subjects)

    post_type = parsed.post_type.lower()
    if category != "academic" and post_type == "resource":
        post_type = "notice"

    graph_payload = NoticeGraphPayload(
        batch_id=batch_id,
        content=content,
        title=parsed.title,
        summary=parsed.summary,
        post_type=post_type,
        event_category=parsed.event_category,
        global_scope=global_scope or "",
        group_name=parsed.group_name or "",
        due_date=parsed.due_date or "",
        subject_id=subject.id if subject else None,
    )
    post_id, event_id = await ingest_faculty_notice(faculty, graph_payload)

    parsed_dict = parsed.model_dump()
    if subject:
        parsed_dict["matched_subject"] = {"code": subject.code, "name": subject.name}

    return PostCreateResponse(
        post_id=post_id,
        message=f"Notice live in knowledge graph — students can ask Jarvis about “{parsed.title}”",
        parsed=parsed_dict,
        event_id=event_id,
        resource_id=None,
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
                event_category=p.get("event_category") or "academic",
                global_scope=p.get("global_scope") or None,
                group_name=p.get("group_name") or None,
                subject_name=r.get("subject_name"),
                subject_code=r.get("subject_code"),
                batch_code=r.get("batch_code"),
                batch_name=r.get("batch_name"),
                due_date=p.get("due_date") or None,
                created_at=created_str,
            )
        )
    return posts

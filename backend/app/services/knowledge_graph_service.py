"""Neo4j knowledge graph — ingest faculty notices for feeds and Jarvis RAG."""

import logging
import uuid
from dataclasses import dataclass

from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver

logger = logging.getLogger("acadmind.knowledge_graph")


@dataclass(frozen=True)
class NoticeGraphPayload:
    batch_id: str
    content: str
    title: str
    summary: str
    post_type: str
    event_category: str
    global_scope: str
    group_name: str
    due_date: str
    subject_id: str | None = None


def build_search_text(payload: NoticeGraphPayload, subject_code: str = "") -> str:
    parts = [
        payload.title,
        payload.summary,
        payload.content,
        payload.event_category,
        payload.global_scope,
        payload.group_name,
        payload.post_type,
        subject_code,
        payload.due_date,
    ]
    return " ".join(p for p in parts if p).lower()


async def _ensure_faculty_node(faculty: AuthUser) -> None:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MERGE (f:Faculty {id: $id})
            SET f.email = $email,
                f.name = coalesce($name, $email),
                f.updated_at = datetime()
            """,
            id=faculty.id,
            email=faculty.email,
            name=faculty.full_name,
        )


async def propagate_batch_to_students(batch_id: str) -> int:
    """Link all students to the batch so new notices appear in feed and Jarvis."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            OPTIONAL MATCH (s:Student)
            WITH b, collect(DISTINCT s) AS students
            UNWIND students AS s
            WITH b, s WHERE s IS NOT NULL
            MERGE (s)-[:MEMBER_OF]->(b)
            WITH b, s
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            FOREACH (_ IN CASE WHEN sub IS NOT NULL THEN [1] ELSE [] END |
                MERGE (s)-[:ENROLLED_IN]->(sub)
            )
            RETURN count(DISTINCT s) AS linked
            """,
            batch_id=batch_id,
        )
        record = await result.single()
        return record["linked"] if record else 0


async def ingest_faculty_notice(
    faculty: AuthUser,
    payload: NoticeGraphPayload,
) -> tuple[str, str | None]:
    """
    Write a faculty notice into the knowledge graph (Post + Event nodes).
    Returns (post_id, event_id).
    """
    await _ensure_faculty_node(faculty)

    post_id = str(uuid.uuid4())
    event_id: str | None = None
    subject_code = ""

    driver = get_neo4j_driver()
    async with driver.session() as session:
        if payload.subject_id:
            sub_result = await session.run(
                "MATCH (sub:Subject {id: $id}) RETURN sub.code AS code",
                id=payload.subject_id,
            )
            sub_record = await sub_result.single()
            if sub_record:
                subject_code = sub_record["code"] or ""

        search_text = build_search_text(payload, subject_code)

        await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            MATCH (f:Faculty {id: $faculty_id})
            CREATE (p:Post {
                id: $post_id,
                content: $content,
                post_type: $post_type,
                event_category: $event_category,
                global_scope: $global_scope,
                group_name: $group_name,
                title: $title,
                summary: $summary,
                search_text: $search_text,
                due_date: $due_date,
                created_at: datetime()
            })
            MERGE (p)-[:FOR_BATCH]->(b)
            MERGE (p)-[:CREATED_BY]->(f)
            """,
            batch_id=payload.batch_id,
            faculty_id=faculty.id,
            post_id=post_id,
            content=payload.content,
            post_type=payload.post_type,
            event_category=payload.event_category,
            global_scope=payload.global_scope,
            group_name=payload.group_name,
            title=payload.title,
            summary=payload.summary,
            search_text=search_text,
            due_date=payload.due_date,
        )

        if payload.subject_id:
            await session.run(
                """
                MATCH (p:Post {id: $post_id}), (sub:Subject {id: $subject_id})
                MERGE (p)-[:FOR_SUBJECT]->(sub)
                """,
                post_id=post_id,
                subject_id=payload.subject_id,
            )

        create_event = (
            payload.post_type in ("exam", "assignment")
            or bool(payload.due_date)
            or payload.event_category in ("cultural", "technical", "global")
        )
        if create_event:
            event_id = str(uuid.uuid4())
            event_type = (
                payload.post_type
                if payload.post_type in ("exam", "assignment")
                else payload.event_category
            )
            await session.run(
                """
                MATCH (p:Post {id: $post_id}), (b:Batch {id: $batch_id})
                CREATE (e:Event {
                    id: $event_id,
                    title: $title,
                    event_type: $event_type,
                    event_category: $event_category,
                    due_date: $due_date,
                    summary: $summary,
                    search_text: $search_text,
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
                batch_id=payload.batch_id,
                event_id=event_id,
                title=payload.title,
                event_type=event_type,
                event_category=payload.event_category,
                due_date=payload.due_date,
                summary=payload.summary,
                search_text=search_text,
                subject_id=payload.subject_id or "",
            )

    linked = await propagate_batch_to_students(payload.batch_id)
    logger.info(
        "Knowledge graph: notice %s ingested for batch %s (%d students linked)",
        post_id,
        payload.batch_id,
        linked,
    )
    return post_id, event_id

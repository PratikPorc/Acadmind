from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import FeedItem
from app.services.demo_seed_service import ensure_demo_enrollment
from app.utils.student_graph import STUDENT_MATCH, student_params


def _feed_item_from_post(raw: dict) -> FeedItem | None:
    if not raw or not raw.get("id"):
        return None
    return FeedItem(
        id=raw["id"],
        title=raw.get("title") or raw.get("content") or "",
        content=raw.get("content") or "",
        item_type=raw.get("item_type") or "notice",
        event_category=raw.get("event_category") or "academic",
        global_scope=raw.get("global_scope") or None,
        group_name=raw.get("group_name") or None,
        subject_code=raw.get("subject_code"),
        batch_code=raw.get("batch_code"),
        due_date=raw.get("due_date") or None,
        created_at=raw.get("created_at"),
    )


async def get_student_feed(student: AuthUser) -> list[FeedItem]:
    await ensure_demo_enrollment(student.id, student.enrollment_id)
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub:Subject)
            RETURN DISTINCT p.id AS id,
                   coalesce(p.title, p.content) AS title,
                   p.content AS content,
                   p.post_type AS item_type,
                   coalesce(p.event_category, 'academic') AS event_category,
                   p.global_scope AS global_scope,
                   p.group_name AS group_name,
                   sub.code AS subject_code,
                   b.code AS batch_code,
                   p.due_date AS due_date,
                   toString(p.created_at) AS created_at
            ORDER BY created_at DESC
            """,
            **student_params(student),
        )
        records = await result.data()

    items: list[FeedItem] = []
    for raw in records:
        item = _feed_item_from_post(raw)
        if item:
            items.append(item)
    return items


async def get_faculty_feed(faculty: AuthUser) -> list[FeedItem]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (f:Faculty {id: $uid})-[:TEACHES]->(b:Batch)
            MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub:Subject)
            RETURN p.id AS id,
                   coalesce(p.title, p.content) AS title,
                   p.content AS content,
                   p.post_type AS item_type,
                   coalesce(p.event_category, 'academic') AS event_category,
                   p.global_scope AS global_scope,
                   p.group_name AS group_name,
                   sub.code AS subject_code,
                   b.code AS batch_code,
                   p.due_date AS due_date,
                   toString(p.created_at) AS created_at
            ORDER BY p.created_at DESC
            LIMIT 50
            """,
            uid=faculty.id,
        )
        records = await result.data()

    return [_feed_item_from_post(r) for r in records if _feed_item_from_post(r)]

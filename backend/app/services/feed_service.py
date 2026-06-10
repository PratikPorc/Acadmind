from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import FeedItem
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
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            OPTIONAL MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[:FOR_SUBJECT]->(sub:Subject)
            OPTIONAL MATCH (e:Event)-[:IN_BATCH]->(b)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(sub2:Subject)
            RETURN collect(DISTINCT {{
                id: p.id,
                title: coalesce(p.title, p.content),
                content: p.content,
                item_type: p.post_type,
                event_category: coalesce(p.event_category, 'academic'),
                global_scope: p.global_scope,
                group_name: p.group_name,
                subject_code: sub.code,
                batch_code: b.code,
                due_date: p.due_date,
                created_at: toString(p.created_at)
            }}) AS posts,
            collect(DISTINCT {{
                id: e.id,
                title: e.title,
                content: e.summary,
                item_type: e.event_type,
                event_category: coalesce(e.event_category, 'academic'),
                global_scope: null,
                group_name: null,
                subject_code: sub2.code,
                batch_code: b.code,
                due_date: e.due_date,
                created_at: toString(e.created_at)
            }}) AS events
            """,
            **student_params(student),
        )
        record = await result.single()

    items: list[FeedItem] = []
    if not record:
        return items

    seen: set[str] = set()
    for group in ("posts", "events"):
        for raw in record[group] or []:
            item = _feed_item_from_post(raw)
            if not item or item.id in seen:
                continue
            seen.add(item.id)
            items.append(item)

    items.sort(key=lambda x: x.created_at or "", reverse=True)
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

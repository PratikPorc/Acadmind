from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import FeedItem
from app.utils.student_graph import STUDENT_MATCH, student_params


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
            OPTIONAL MATCH (r:Resource)-[:FOR_BATCH]->(b)
            RETURN collect(DISTINCT {
                id: p.id,
                title: coalesce(p.title, p.content),
                content: p.content,
                item_type: p.post_type,
                subject_code: sub.code,
                batch_code: b.code,
                due_date: p.due_date,
                file_name: p.file_name,
                created_at: toString(p.created_at)
            }) AS posts,
            collect(DISTINCT {
                id: e.id,
                title: e.title,
                content: e.summary,
                item_type: e.event_type,
                subject_code: sub2.code,
                batch_code: b.code,
                due_date: e.due_date,
                file_name: null,
                created_at: toString(e.created_at)
            }) AS events,
            collect(DISTINCT {
                id: r.id,
                title: r.title,
                content: r.file_name,
                item_type: 'resource',
                subject_code: null,
                batch_code: b.code,
                due_date: null,
                file_name: r.file_name,
                created_at: toString(r.created_at)
            }) AS resources
            """,
            **student_params(student),
        )
        record = await result.single()

    items: list[FeedItem] = []
    if not record:
        return items

    for group in ("posts", "events", "resources"):
        for raw in record[group] or []:
            if not raw or not raw.get("id"):
                continue
            items.append(FeedItem(**raw))

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
                   sub.code AS subject_code,
                   b.code AS batch_code,
                   p.due_date AS due_date,
                   p.file_name AS file_name,
                   toString(p.created_at) AS created_at
            ORDER BY p.created_at DESC
            LIMIT 50
            """,
            uid=faculty.id,
        )
        records = await result.data()

    return [FeedItem(**r) for r in records if r.get("id")]

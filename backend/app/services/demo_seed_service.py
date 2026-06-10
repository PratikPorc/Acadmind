import logging
from dataclasses import dataclass

from app.constants.campus import CAMPUS_CLUBS, CAMPUS_DOMAINS
from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import UserRole
from app.services.knowledge_graph_service import NoticeGraphPayload, build_search_text

logger = logging.getLogger("acadmind.demo")

DEMO_BATCH_ID = "00000000-0000-4000-8000-000000000001"
DEMO_FACULTY_ID = "00000000-0000-4000-8000-000000000099"
DEMO_MARKER = "acadmind-demo-v1"


@dataclass(frozen=True)
class DemoPost:
    slug: str
    title: str
    content: str
    post_type: str
    event_category: str
    subject_code: str | None = None
    group_name: str | None = None
    global_scope: str | None = None
    due_date: str = ""


DEMO_SUBJECTS: tuple[tuple[str, str], ...] = (
    ("CN", "Computer Networks"),
    ("SE", "Software Engineering"),
    ("DS", "Data Structures"),
)

DEMO_POSTS: tuple[DemoPost, ...] = (
    DemoPost(
        slug="cn-midterm",
        title="CN Mid-Term Examination",
        content="Computer Networks mid-term exam on 15 July 2026 in Hall A. Syllabus: chapters 1–5.",
        post_type="exam",
        event_category="academic",
        subject_code="CN",
        due_date="2026-07-15",
    ),
    DemoPost(
        slug="se-assignment-4",
        title="SE Assignment 4 — Design Patterns",
        content="Software Engineering Assignment 4 on design patterns is due 20 June 2026. Submit PDF on portal.",
        post_type="assignment",
        event_category="academic",
        subject_code="SE",
        due_date="2026-06-20",
    ),
    DemoPost(
        slug="ds-lab-test",
        title="DS Lab Test — Trees & Graphs",
        content="Data Structures lab test on trees and graphs on 25 June 2026 during lab hours.",
        post_type="exam",
        event_category="academic",
        subject_code="DS",
        due_date="2026-06-25",
    ),
    DemoPost(
        slug="dance-fest",
        title="Dance Club — Inter-College Fest",
        content="Dance Club auditions for Inter-College Fest on 25 June 2026 at the auditorium. Register with the club desk.",
        post_type="notice",
        event_category="cultural",
        group_name="Dance Club",
        due_date="2026-06-25",
    ),
    DemoPost(
        slug="music-open-mic",
        title="Music Club Open Mic Night",
        content="Music Club Open Mic Night on 18 June 2026 at 6 PM in the amphitheatre. All students welcome.",
        post_type="notice",
        event_category="cultural",
        group_name="Music Club",
        due_date="2026-06-18",
    ),
    DemoPost(
        slug="ai-hackathon",
        title="AI & ML Hackathon 2026",
        content="48-hour AI & Machine Learning hackathon on 10–11 July 2026. Teams of 3–4. Register by 5 July.",
        post_type="notice",
        event_category="technical",
        group_name="AI & Machine Learning",
        due_date="2026-07-11",
    ),
    DemoPost(
        slug="web-workshop",
        title="Web Development Workshop",
        content="Web Development workshop on React and APIs on 22 June 2026. Limited seats — register with the domain lead.",
        post_type="notice",
        event_category="technical",
        group_name="Web Development",
        due_date="2026-06-22",
    ),
    DemoPost(
        slug="midsem-break",
        title="Mid-Semester Break",
        content="Mid-semester break from 16 June to 20 June 2026. Regular classes resume 23 June.",
        post_type="notice",
        event_category="global",
        global_scope="academic",
        due_date="2026-06-16",
    ),
    DemoPost(
        slug="spring-fest",
        title="Spring Fest 2026 Registration",
        content="Annual Spring Fest registration is open until 30 June 2026. Cultural events, food stalls, and concerts.",
        post_type="notice",
        event_category="global",
        global_scope="cultural",
        due_date="2026-06-30",
    ),
    DemoPost(
        slug="tech-summit",
        title="Campus Tech Summit",
        content="Techno India University Tech Summit on 5 July 2026 — keynote talks, project expo, and networking.",
        post_type="notice",
        event_category="global",
        global_scope="technical",
        due_date="2026-07-05",
    ),
)


def _subject_id(code: str) -> str:
    return f"{DEMO_BATCH_ID}-subject-{code.lower()}"


def _post_id(slug: str) -> str:
    return f"{DEMO_BATCH_ID}-post-{slug}"


async def clear_demo_data() -> None:
    """Remove demo batch, notices, and marker (keeps students/faculty/users)."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            OPTIONAL MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (e:Event)-[:IN_BATCH]->(b)
            OPTIONAL MATCH (e2:Event)-[:FROM_POST]->(p)
            OPTIONAL MATCH (b)-[:HAS_DEMO]->(m:DemoMarker)
            DETACH DELETE sub, p, e, e2, m, b
            """,
            batch_id=DEMO_BATCH_ID,
        )
        await session.run(
            """
            MATCH (p:Post)
            WHERE p.demo = true OR p.id STARTS WITH $batch_prefix
            OPTIONAL MATCH (e:Event)-[:FROM_POST]->(p)
            DETACH DELETE e, p
            """,
            batch_prefix=f"{DEMO_BATCH_ID}-post-",
        )
        await session.run(
            """
            MATCH (e:Event)
            WHERE e.demo = true OR e.id STARTS WITH $batch_prefix
            DETACH DELETE e
            """,
            batch_prefix=f"{DEMO_BATCH_ID}-post-",
        )
        await session.run("MATCH (m:DemoMarker) DETACH DELETE m")
    logger.info("Demo graph data cleared")


async def is_demo_seeded() -> bool:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})-[:HAS_DEMO]->(:DemoMarker {version: $marker})
            RETURN b.id AS id
            LIMIT 1
            """,
            batch_id=DEMO_BATCH_ID,
            marker=DEMO_MARKER,
        )
        return (await result.single()) is not None


async def find_primary_faculty() -> AuthUser | None:
    """Return the first real faculty account in the graph (excludes the placeholder demo id)."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (f:Faculty)
            WHERE f.id <> $demo_id
            RETURN f.id AS id, f.email AS email, f.name AS name
            ORDER BY coalesce(f.updated_at, datetime()) DESC
            LIMIT 1
            """,
            demo_id=DEMO_FACULTY_ID,
        )
        record = await result.single()
        if not record:
            return None
        return AuthUser(
            id=record["id"],
            email=record["email"] or "",
            role=UserRole.faculty,
            full_name=record["name"],
        )


async def ensure_demo_faculty_access(faculty: AuthUser) -> None:
    """Attach demo batch and notices to the logged-in faculty account."""
    if not await is_demo_seeded():
        return

    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            MATCH (f:Faculty {id: $faculty_id})
            MERGE (f)-[:TEACHES]->(b)
            SET b.demo_owner_id = $faculty_id
            WITH b, f
            MATCH (p:Post)-[:FOR_BATCH]->(b)
            OPTIONAL MATCH (p)-[old:CREATED_BY]->(:Faculty)
            DELETE old
            MERGE (p)-[:CREATED_BY]->(f)
            """,
            batch_id=DEMO_BATCH_ID,
            faculty_id=faculty.id,
        )
        await session.run(
            """
            MATCH (f:Faculty {id: $demo_id})-[r:TEACHES]->(b:Batch {id: $batch_id})
            WHERE $demo_id <> $faculty_id
            DELETE r
            """,
            demo_id=DEMO_FACULTY_ID,
            batch_id=DEMO_BATCH_ID,
            faculty_id=faculty.id,
        )
    logger.info("Demo batch linked to faculty %s", faculty.email)


async def seed_demo_once() -> dict[str, int | str] | None:
    """Apply demo seed exactly once (skipped if marker already exists)."""
    if await is_demo_seeded():
        logger.info("Demo seed already present — skipping")
        return None

    faculty = await find_primary_faculty()
    if not faculty:
        logger.info("No faculty in graph yet — demo seed deferred until faculty login")
        return None

    result = await seed_demo_for_faculty(faculty)
    logger.info("One-time demo seed completed for faculty %s", faculty.email)
    return result


async def seed_demo_for_faculty_if_needed(faculty: AuthUser) -> dict[str, int | str] | None:
    """Seed demo data on first faculty login when startup seed was deferred."""
    if await is_demo_seeded():
        await ensure_demo_faculty_access(faculty)
        return None
    return await seed_demo_for_faculty(faculty)


async def seed_demo_for_faculty(faculty: AuthUser) -> dict[str, int | str]:
    """Idempotent demo seed owned by the logged-in faculty account."""
    driver = get_neo4j_driver()
    subject_ids = {code: _subject_id(code) for code, _ in DEMO_SUBJECTS}

    async with driver.session() as session:
        await session.run(
            """
            MERGE (f:Faculty {id: $faculty_id})
            SET f.email = $faculty_email,
                f.name = coalesce($faculty_name, $faculty_email)
            MERGE (b:Batch {id: $batch_id})
            ON CREATE SET
                b.name = 'CSE 6A Demo',
                b.code = 'CSE6A',
                b.semester = 'VI',
                b.branch = 'CSE',
                b.created_at = datetime()
            MERGE (f)-[:TEACHES]->(b)
            MERGE (b)-[:HAS_DEMO]->(m:DemoMarker {version: $marker})
            """,
            faculty_id=faculty.id,
            faculty_email=faculty.email,
            faculty_name=faculty.full_name,
            batch_id=DEMO_BATCH_ID,
            marker=DEMO_MARKER,
        )

        for code, name in DEMO_SUBJECTS:
            sub_id = subject_ids[code]
            await session.run(
                """
                MATCH (b:Batch {id: $batch_id})
                MERGE (sub:Subject {id: $sub_id})
                SET sub.name = $name,
                    sub.code = $code,
                    sub.batch_id = $batch_id
                MERGE (b)-[:HAS_SUBJECT]->(sub)
                """,
                batch_id=DEMO_BATCH_ID,
                sub_id=sub_id,
                name=name,
                code=code,
            )

        for post in DEMO_POSTS:
            post_id = _post_id(post.slug)
            event_id = f"{post_id}-event"
            graph_payload = NoticeGraphPayload(
                batch_id=DEMO_BATCH_ID,
                content=post.content,
                title=post.title,
                summary=post.content,
                post_type=post.post_type,
                event_category=post.event_category,
                global_scope=post.global_scope or "",
                group_name=post.group_name or "",
                due_date=post.due_date,
                subject_id=subject_ids.get(post.subject_code or "") if post.subject_code else None,
            )
            search_text = build_search_text(graph_payload, post.subject_code or "")
            await session.run(
                """
                MATCH (b:Batch {id: $batch_id})
                MATCH (f:Faculty {id: $faculty_id})
                MERGE (p:Post {id: $post_id})
                SET p.content = $content,
                    p.post_type = $post_type,
                    p.event_category = $event_category,
                    p.global_scope = $global_scope,
                    p.group_name = $group_name,
                    p.title = $title,
                    p.summary = $summary,
                    p.search_text = $search_text,
                    p.due_date = $due_date,
                    p.demo = true,
                    p.demo_slug = $demo_slug,
                    p.created_at = coalesce(p.created_at, datetime())
                MERGE (p)-[:FOR_BATCH]->(b)
                MERGE (p)-[:CREATED_BY]->(f)
                WITH p, b
                MERGE (e:Event {id: $event_id})
                SET e.title = $title,
                    e.event_type = $post_type,
                    e.event_category = $event_category,
                    e.due_date = $due_date,
                    e.summary = $summary,
                    e.search_text = $search_text,
                    e.demo = true,
                    e.created_at = coalesce(e.created_at, datetime())
                MERGE (e)-[:FROM_POST]->(p)
                MERGE (e)-[:IN_BATCH]->(b)
                """,
                batch_id=DEMO_BATCH_ID,
                faculty_id=faculty.id,
                post_id=post_id,
                event_id=event_id,
                content=post.content,
                post_type=post.post_type,
                event_category=post.event_category,
                global_scope=post.global_scope or "",
                group_name=post.group_name or "",
                title=post.title,
                summary=post.content,
                search_text=search_text,
                due_date=post.due_date,
                demo_slug=post.slug,
            )

            if post.subject_code and post.subject_code in subject_ids:
                await session.run(
                    """
                    MATCH (p:Post {id: $post_id}), (sub:Subject {id: $sub_id})
                    MERGE (p)-[:FOR_SUBJECT]->(sub)
                    WITH p, sub
                    MATCH (e:Event {id: $event_id})
                    MERGE (e)-[:BELONGS_TO]->(sub)
                    """,
                    post_id=post_id,
                    sub_id=subject_ids[post.subject_code],
                    event_id=event_id,
                )

        link_result = await session.run(
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
            RETURN count(DISTINCT s) AS students_linked
            """,
            batch_id=DEMO_BATCH_ID,
        )
        link_record = await link_result.single()
        students_linked = link_record["students_linked"] if link_record else 0

    logger.info(
        "Demo seeded by faculty %s — %d posts, %d students linked",
        faculty.email,
        len(DEMO_POSTS),
        students_linked,
    )
    return {
        "batch_id": DEMO_BATCH_ID,
        "batch_code": "CSE6A",
        "posts_seeded": len(DEMO_POSTS),
        "students_linked": students_linked,
        "message": "Demo notices seeded for academic, cultural, technical & global sections",
    }


async def ensure_demo_enrollment(user_id: str | None, enrollment_id: str | None) -> None:
    """Link a student to the demo batch when it exists."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        exists = await session.run(
            "MATCH (b:Batch {id: $batch_id}) RETURN b.id AS id",
            batch_id=DEMO_BATCH_ID,
        )
        if not await exists.single():
            return

        if user_id:
            await session.run(
                """
                MATCH (b:Batch {id: $batch_id})
                OPTIONAL MATCH (s:Student {id: $uid})
                FOREACH (_ IN CASE WHEN s IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (s)-[:MEMBER_OF]->(b)
                )
                WITH b
                OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
                OPTIONAL MATCH (s:Student {id: $uid})-[:MEMBER_OF]->(b)
                FOREACH (_ IN CASE WHEN s IS NOT NULL AND sub IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (s)-[:ENROLLED_IN]->(sub)
                )
                """,
                batch_id=DEMO_BATCH_ID,
                uid=user_id,
            )
        if enrollment_id:
            await session.run(
                """
                MATCH (b:Batch {id: $batch_id})
                MERGE (s:Student {enrollment_id: $enrollment_id})
                SET s.id = coalesce(s.id, $uid)
                MERGE (s)-[:MEMBER_OF]->(b)
                WITH b, s
                OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
                FOREACH (_ IN CASE WHEN sub IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (s)-[:ENROLLED_IN]->(sub)
                )
                """,
                batch_id=DEMO_BATCH_ID,
                enrollment_id=enrollment_id,
                uid=user_id or "",
            )


def demo_group_names(category: str) -> list[str]:
    if category == "cultural":
        return list(CAMPUS_CLUBS)
    if category == "technical":
        return list(CAMPUS_DOMAINS)
    return []

import logging
import uuid
from typing import Any

from fastapi import HTTPException, status

from app.constants.campus import CAMPUS_CLUBS, CAMPUS_DOMAINS
from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import (
    BatchCreate,
    BatchDetail,
    BatchResponse,
    CampusGroupResponse,
    StudentSubjectResponse,
    SubjectCreate,
    SubjectResponse,
)
from app.utils.enrollment import normalize_enrollment_id
from app.utils.student_graph import STUDENT_MATCH, student_params

logger = logging.getLogger("acadmind.batch")


async def create_batch(faculty: AuthUser, payload: BatchCreate) -> BatchResponse:
    batch_id = str(uuid.uuid4())
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MERGE (f:Faculty {id: $faculty_id})
            SET f.email = $faculty_email,
                f.name = coalesce($faculty_name, $faculty_email)
            CREATE (b:Batch {
                id: $id,
                name: $name,
                code: $code,
                semester: $semester,
                branch: $branch,
                created_at: datetime()
            })
            MERGE (f)-[:TEACHES]->(b)
            """,
            faculty_id=faculty.id,
            faculty_email=faculty.email,
            faculty_name=faculty.full_name,
            id=batch_id,
            name=payload.name,
            code=payload.code.upper(),
            semester=payload.semester,
            branch=payload.branch,
        )
    return BatchResponse(
        id=batch_id,
        name=payload.name,
        code=payload.code.upper(),
        semester=payload.semester,
        branch=payload.branch,
    )


async def list_batches_for_user(user: AuthUser) -> list[BatchResponse]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        if user.role.value == "faculty":
            result = await session.run(
                """
                MATCH (f:Faculty {id: $uid})-[:TEACHES]->(b:Batch)
                OPTIONAL MATCH (b)<-[:MEMBER_OF]-(s:Student)
                OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
                RETURN b, count(DISTINCT s) AS student_count, count(DISTINCT sub) AS subject_count
                ORDER BY b.created_at DESC
                """,
                uid=user.id,
            )
        else:
            result = await session.run(
                f"""
                {STUDENT_MATCH}
                MATCH (s)-[:MEMBER_OF]->(b:Batch)
                OPTIONAL MATCH (b)<-[:MEMBER_OF]-(st:Student)
                OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
                RETURN b, count(DISTINCT st) AS student_count, count(DISTINCT sub) AS subject_count
                ORDER BY b.created_at DESC
                """,
                **student_params(user),
            )
        records = await result.data()
    return [_batch_from_record(r) for r in records]


async def get_batch_detail(batch_id: str, user: AuthUser) -> BatchDetail:
    await _assert_batch_access(batch_id, user)
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            OPTIONAL MATCH (b)<-[:MEMBER_OF]-(s:Student)
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            RETURN b,
                   collect(DISTINCT s.enrollment_id) AS student_enrollment_ids,
                   collect(DISTINCT {
                       id: sub.id,
                       name: sub.name,
                       code: sub.code,
                       batch_id: $batch_id
                   }) AS subjects,
                   count(DISTINCT s) AS student_count,
                   count(DISTINCT sub) AS subject_count
            """,
            batch_id=batch_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

        batch = record["b"]
        subjects_raw = [s for s in record["subjects"] if s.get("id")]
        subjects = [SubjectResponse(**s) for s in subjects_raw]
        student_enrollment_ids = [eid for eid in record["student_enrollment_ids"] if eid]

    return BatchDetail(
        id=batch["id"],
        name=batch["name"],
        code=batch["code"],
        semester=batch.get("semester", ""),
        branch=batch.get("branch", ""),
        student_count=record["student_count"],
        subject_count=record["subject_count"],
        subjects=subjects,
        student_enrollment_ids=student_enrollment_ids,
    )


async def add_subject(batch_id: str, faculty: AuthUser, payload: SubjectCreate) -> SubjectResponse:
    await _assert_faculty_owns_batch(batch_id, faculty.id)
    subject_id = str(uuid.uuid4())
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            CREATE (sub:Subject {
                id: $id,
                name: $name,
                code: $code,
                batch_id: $batch_id
            })
            MERGE (b)-[:HAS_SUBJECT]->(sub)
            WITH b, sub
            OPTIONAL MATCH (b)<-[:MEMBER_OF]-(s:Student)
            FOREACH (_ IN CASE WHEN s IS NOT NULL THEN [1] ELSE [] END |
                MERGE (s)-[:ENROLLED_IN]->(sub)
            )
            """,
            batch_id=batch_id,
            id=subject_id,
            name=payload.name,
            code=payload.code.upper(),
        )
    return SubjectResponse(
        id=subject_id,
        name=payload.name,
        code=payload.code.upper(),
        batch_id=batch_id,
    )


async def add_student_to_batch(
    batch_id: str, faculty: AuthUser, enrollment_id: str
) -> dict[str, str]:
    await _assert_faculty_owns_batch(batch_id, faculty.id)
    try:
        enrollment_id = normalize_enrollment_id(enrollment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})
            MERGE (s:Student {enrollment_id: $enrollment_id})
            MERGE (s)-[:MEMBER_OF]->(b)
            WITH s, b
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            FOREACH (_ IN CASE WHEN sub IS NOT NULL THEN [1] ELSE [] END |
                MERGE (s)-[:ENROLLED_IN]->(sub)
            )
            RETURN s.enrollment_id AS id
            """,
            batch_id=batch_id,
            enrollment_id=enrollment_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    logger.info("Student %s linked to batch %s", enrollment_id, batch_id)
    return {
        "message": "Student linked to batch",
        "enrollment_id": enrollment_id,
    }


async def remove_student_from_batch(
    batch_id: str, faculty: AuthUser, enrollment_id: str
) -> dict[str, str]:
    await _assert_faculty_owns_batch(batch_id, faculty.id)
    try:
        enrollment_id = normalize_enrollment_id(enrollment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})<-[m:MEMBER_OF]-(s:Student {enrollment_id: $enrollment_id})
            OPTIONAL MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(sub)
            DELETE e, m
            RETURN s.enrollment_id AS id
            """,
            batch_id=batch_id,
            enrollment_id=enrollment_id,
        )
        record = await result.single()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found in this batch",
            )
    logger.info("Student %s removed from batch %s", enrollment_id, batch_id)
    return {
        "message": "Student removed from batch",
        "enrollment_id": enrollment_id,
    }


async def get_batch_subjects(batch_id: str) -> list[SubjectResponse]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (b:Batch {id: $batch_id})-[:HAS_SUBJECT]->(sub:Subject)
            RETURN sub
            ORDER BY sub.code
            """,
            batch_id=batch_id,
        )
        records = await result.data()
    return [
        SubjectResponse(
            id=r["sub"]["id"],
            name=r["sub"]["name"],
            code=r["sub"]["code"],
            batch_id=batch_id,
        )
        for r in records
    ]


async def _assert_faculty_owns_batch(batch_id: str, faculty_id: str) -> None:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (f:Faculty {id: $faculty_id})-[:TEACHES]->(b:Batch {id: $batch_id})
            RETURN b.id AS id
            """,
            faculty_id=faculty_id,
            batch_id=batch_id,
        )
        if not await result.single():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your batch")


async def _assert_batch_access(batch_id: str, user: AuthUser) -> None:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        if user.role.value == "faculty":
            result = await session.run(
                """
                MATCH (f:Faculty {id: $uid})-[:TEACHES]->(b:Batch {id: $batch_id})
                RETURN b.id AS id
                """,
                uid=user.id,
                batch_id=batch_id,
            )
        else:
            result = await session.run(
                f"""
                {STUDENT_MATCH}
                MATCH (s)-[:MEMBER_OF]->(b:Batch {{id: $batch_id}})
                RETURN b.id AS id
                """,
                batch_id=batch_id,
                **student_params(user),
            )
        if not await result.single():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Batch access denied")


async def list_student_subjects(student: AuthUser) -> list[StudentSubjectResponse]:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            MATCH (b)-[:HAS_SUBJECT]->(sub:Subject)
            MERGE (s)-[:ENROLLED_IN]->(sub)
            """,
            **student_params(student),
        )
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:ENROLLED_IN]->(sub:Subject)
            OPTIONAL MATCH (b:Batch)-[:HAS_SUBJECT]->(sub)
            RETURN DISTINCT sub.id AS id,
                   sub.name AS name,
                   sub.code AS code,
                   sub.batch_id AS batch_id,
                   b.code AS batch_code
            ORDER BY sub.code
            """,
            **student_params(student),
        )
        records = await result.data()
    return [StudentSubjectResponse(**r) for r in records if r.get("id")]


async def list_campus_groups(student: AuthUser, category: str) -> list[CampusGroupResponse]:
    if category not in ("cultural", "technical"):
        return []
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            f"""
            {STUDENT_MATCH}
            MATCH (s)-[:MEMBER_OF]->(b:Batch)
            MATCH (p:Post)-[:FOR_BATCH]->(b)
            WHERE p.event_category = $category AND coalesce(p.group_name, '') <> ''
            RETURN DISTINCT p.group_name AS name
            ORDER BY name
            """,
            category=category,
            **student_params(student),
        )
        records = await result.data()
    from_posts = [CampusGroupResponse(name=r["name"]) for r in records if r.get("name")]
    if from_posts:
        return from_posts
    defaults = CAMPUS_CLUBS if category == "cultural" else CAMPUS_DOMAINS
    return [CampusGroupResponse(name=name) for name in defaults]


def _batch_from_record(record: dict[str, Any]) -> BatchResponse:
    batch = record["b"]
    return BatchResponse(
        id=batch["id"],
        name=batch["name"],
        code=batch["code"],
        semester=batch.get("semester", ""),
        branch=batch.get("branch", ""),
        student_count=record.get("student_count", 0),
        subject_count=record.get("subject_count", 0),
    )

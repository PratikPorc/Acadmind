from app.core.security import AuthUser
from app.db.neo4j import get_neo4j_driver
from app.models.schemas import UserProfile, UserRole


async def sync_user_to_graph(user: AuthUser) -> None:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run(
            """
            MERGE (u:User {id: $id})
            SET u.email = $email,
                u.role = $role,
                u.full_name = $full_name,
                u.semester = $semester,
                u.branch = $branch,
                u.enrollment_id = $enrollment_id,
                u.updated_at = datetime()
            """,
            id=user.id,
            email=user.email,
            role=user.role.value,
            full_name=user.full_name or "",
            semester=user.semester or "",
            branch=user.branch or "",
            enrollment_id=user.enrollment_id or "",
        )

        if user.role == UserRole.student and user.enrollment_id:
            await session.run(
                """
                MERGE (s:Student {enrollment_id: $enrollment_id})
                SET s.id = $id,
                    s.email = $email,
                    s.full_name = $full_name,
                    s.semester = $semester,
                    s.branch = $branch,
                    s.updated_at = datetime()
                WITH s
                MATCH (u:User {id: $id})
                MERGE (u)-[:IS_STUDENT]->(s)
                """,
                enrollment_id=user.enrollment_id,
                id=user.id,
                email=user.email,
                full_name=user.full_name or "",
                semester=user.semester or "",
                branch=user.branch or "",
            )
        elif user.role == UserRole.faculty:
            await session.run(
                """
                MERGE (f:Faculty {id: $id})
                SET f.email = $email,
                    f.name = coalesce($full_name, $email),
                    f.updated_at = datetime()
                WITH f
                MATCH (u:User {id: $id})
                MERGE (u)-[:IS_FACULTY]->(f)
                """,
                id=user.id,
                email=user.email,
                full_name=user.full_name,
            )


def to_profile(user: AuthUser) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        semester=user.semester,
        branch=user.branch,
        enrollment_id=user.enrollment_id,
    )

from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

_driver: AsyncDriver | None = None


def init_neo4j_driver(settings: Any) -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


async def close_neo4j_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


def get_neo4j_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver is not initialized")
    return _driver


async def check_neo4j_connection() -> tuple[bool, str]:
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            if record and record["ok"] == 1:
                return True, "connected"
            return False, "unexpected response"
    except RuntimeError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)

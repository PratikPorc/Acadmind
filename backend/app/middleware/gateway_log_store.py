from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any


@dataclass
class GatewayLogEntry:
    request_id: str
    method: str
    path: str
    query: str
    status_code: int
    duration_ms: float
    client_ip: str
    user_email: str | None = None
    user_role: str | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class GatewayLogStore:
    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._entries: deque[GatewayLogEntry] = deque(maxlen=max_entries)
        self._lock = Lock()

    def configure(self, max_entries: int) -> None:
        if max_entries == self._max_entries:
            return
        with self._lock:
            self._max_entries = max_entries
            self._entries = deque(self._entries, maxlen=max_entries)

    def add(self, entry: GatewayLogEntry) -> None:
        with self._lock:
            self._entries.appendleft(entry)

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._entries)[:limit]
        return [asdict(item) for item in items]


gateway_log_store = GatewayLogStore()


def configure_gateway_log_store(max_entries: int) -> None:
    gateway_log_store.configure(max_entries)

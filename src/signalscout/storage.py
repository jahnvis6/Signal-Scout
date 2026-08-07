"""SQLite persistence for watches. Swappable for Postgres later by
reimplementing this same interface against SQLAlchemy.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, List, Optional

from .models import ConditionType, Watch

SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    keyword TEXT,
    check_interval_minutes INTEGER NOT NULL,
    notify_webhook_url TEXT,
    last_snapshot TEXT,
    last_checked_at TEXT,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
"""


class WatchStore:
    """CRUD + snapshot updates for Watch records."""

    def __init__(self, db_path: str = "signalscout.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def add(self, watch: Watch) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO watches
                   (id, name, url, condition_type, keyword, check_interval_minutes,
                    notify_webhook_url, last_snapshot, last_checked_at, created_at, active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    watch.id,
                    watch.name,
                    watch.url,
                    watch.condition_type.value,
                    watch.keyword,
                    watch.check_interval_minutes,
                    watch.notify_webhook_url,
                    watch.last_snapshot,
                    watch.last_checked_at,
                    watch.created_at,
                    int(watch.active),
                ),
            )

    def get(self, watch_id: str) -> Optional[Watch]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM watches WHERE id = ?", (watch_id,)).fetchone()
            return self._row_to_watch(row) if row else None

    def list_all(self, active_only: bool = True) -> List[Watch]:
        with self._connect() as conn:
            query = "SELECT * FROM watches"
            if active_only:
                query += " WHERE active = 1"
            rows = conn.execute(query).fetchall()
            return [self._row_to_watch(row) for row in rows]

    def update_snapshot(self, watch_id: str, snapshot: str, checked_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE watches SET last_snapshot = ?, last_checked_at = ? WHERE id = ?",
                (snapshot, checked_at, watch_id),
            )

    def deactivate(self, watch_id: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE watches SET active = 0 WHERE id = ?", (watch_id,))

    def delete(self, watch_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM watches WHERE id = ?", (watch_id,))

    @staticmethod
    def _row_to_watch(row: sqlite3.Row) -> Watch:
        return Watch(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            condition_type=ConditionType(row["condition_type"]),
            keyword=row["keyword"],
            check_interval_minutes=row["check_interval_minutes"],
            notify_webhook_url=row["notify_webhook_url"],
            last_snapshot=row["last_snapshot"],
            last_checked_at=row["last_checked_at"],
            created_at=row["created_at"],
            active=bool(row["active"]),
        )
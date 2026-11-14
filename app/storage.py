"""SQLite persistence for samples, proposals, and append-only audit events."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class SQLiteStore:
    """Small local MVP repository; use PostgreSQL for a multi-node deployment."""

    def __init__(self, path: str | Path | None = None):
        configured = str(path or os.getenv("HARIRSMART_DB_PATH", "data/harirsmart.db"))
        self.path = configured
        if configured != ":memory:":
            Path(configured).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            if self.path != ":memory:":
                connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS samples (
                    sample_id TEXT PRIMARY KEY,
                    source_timestamp TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    quality_json TEXT NOT NULL,
                    dvr_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_samples_received_at
                    ON samples(received_at DESC);
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    sample_id TEXT,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_audit_timestamp
                    ON audit_events(timestamp DESC);
                """
            )
            connection.commit()

    def save_sample(self, record: dict[str, Any]) -> None:
        sample = record["sample"]
        with self._connection() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO samples
                   (sample_id, source_timestamp, received_at, source,
                    payload_json, quality_json, dvr_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record["sample_id"],
                    str(sample.get("timestamp", "")),
                    record["received_at"],
                    str(sample.get("source", "unknown")),
                    json.dumps(sample, ensure_ascii=False, allow_nan=True),
                    json.dumps(record["quality"], ensure_ascii=False, allow_nan=True),
                    json.dumps(record["dvr"], ensure_ascii=False, allow_nan=True),
                ),
            )
            connection.commit()

    def save_proposal(self, proposal: dict[str, Any], sample_id: str | None) -> None:
        with self._connection() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO proposals
                   (proposal_id, sample_id, created_at, payload_json)
                   VALUES (?, ?, ?, ?)""",
                (
                    proposal["proposal_id"],
                    sample_id,
                    proposal.get("created_at", ""),
                    json.dumps(proposal, ensure_ascii=False, allow_nan=True),
                ),
            )
            connection.commit()

    def append_audit(self, event: dict[str, Any]) -> None:
        with self._connection() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO audit_events
                   (event_id, timestamp, actor, action, object_id, payload_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event["event_id"],
                    event["timestamp"],
                    event["actor"],
                    event["action"],
                    event["object_id"],
                    json.dumps(event, ensure_ascii=False, allow_nan=True),
                ),
            )
            connection.commit()

    def list_samples(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 500))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM samples ORDER BY received_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [
            {
                "sample_id": row["sample_id"],
                "sample": json.loads(row["payload_json"]),
                "quality": json.loads(row["quality_json"]),
                "dvr": json.loads(row["dvr_json"]),
                "received_at": row["received_at"],
            }
            for row in rows
        ]

    def list_audit(self, limit: int = 200) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 1000))
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM audit_events ORDER BY timestamp DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def counts(self) -> dict[str, int]:
        with self._connection() as connection:
            return {
                "samples": connection.execute("SELECT COUNT(*) FROM samples").fetchone()[0],
                "proposals": connection.execute("SELECT COUNT(*) FROM proposals").fetchone()[0],
                "audit_events": connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0],
            }

    def clear(self) -> None:
        """Clear local state for isolated tests; never exposed as an API operation."""
        with self._connection() as connection:
            connection.executescript(
                "DELETE FROM samples; DELETE FROM proposals; DELETE FROM audit_events;"
            )
            connection.commit()

"""SQLite-backed Idempotency & Deduplication Storage Engine (ENG-0002)."""
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from .. import config
except (ImportError, ValueError):
    import config


class IdempotencyStore:
    """Provides atomic lock acquisition and cached response retrieval for state-mutating actions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (config.REPO_ROOT / ".adk" / "idempotency.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a sqlite connection with row access."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema with primary key and expiration indexes."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_records (
                    idempotency_key TEXT PRIMARY KEY,
                    action_name TEXT NOT NULL,
                    request_params TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_payload TEXT,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_idempotency_expires
                ON idempotency_records(expires_at)
                """
            )
            conn.commit()

    @staticmethod
    def generate_key(session_id: str, action: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic SHA-256 idempotency key based on transaction intent."""
        serialized_params = json.dumps(params, sort_keys=True)
        raw = f"{session_id}:{action}:{serialized_params}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_or_lock(
        self,
        key: str,
        action: str,
        params: Dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Atomically inspects the idempotency key state."""
        now = time.time()
        expires_at = now + ttl_seconds
        serialized_params = json.dumps(params, sort_keys=True)

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT status, response_payload, expires_at FROM idempotency_records WHERE idempotency_key = ?",
                (key,),
            )
            row = cursor.fetchone()

            if row:
                status = row["status"]
                payload_str = row["response_payload"]
                exp = row["expires_at"]

                if now > exp:
                    conn.execute("DELETE FROM idempotency_records WHERE idempotency_key = ?", (key,))
                elif status == "COMPLETED" and payload_str:
                    return "COMPLETED", json.loads(payload_str)
                elif status == "IN_PROGRESS":
                    return "IN_PROGRESS", None

            try:
                conn.execute(
                    """
                    INSERT INTO idempotency_records 
                    (idempotency_key, action_name, request_params, status, response_payload, created_at, expires_at)
                    VALUES (?, ?, ?, 'IN_PROGRESS', NULL, ?, ?)
                    """,
                    (key, action, serialized_params, now, expires_at),
                )
                conn.commit()
                return "NEW", None
            except sqlite3.IntegrityError:
                return "IN_PROGRESS", None

    def complete(self, key: str, response_payload: Dict[str, Any]) -> None:
        """Mark idempotency record as COMPLETED and store response payload."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE idempotency_records
                SET status = 'COMPLETED', response_payload = ?
                WHERE idempotency_key = ?
                """,
                (json.dumps(response_payload), key),
            )
            conn.commit()

    def fail(self, key: str, error_message: str) -> None:
        """Mark idempotency record as FAILED."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE idempotency_records
                SET status = 'FAILED', response_payload = ?
                WHERE idempotency_key = ?
                """,
                (json.dumps({"error": error_message}), key),
            )
            conn.commit()

    def clear(self) -> None:
        """Clear all records (for testing)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM idempotency_records")
            conn.commit()

import csv
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from core.models import ScanResult, SessionRow, SiteMap


class HistoryManager:
    def __init__(self, db_path: str = "db/history.sqlite"):
        self._db_path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                      id          INTEGER PRIMARY KEY AUTOINCREMENT,
                      target_url  TEXT NOT NULL,
                      started_at  TEXT NOT NULL,
                      ended_at    TEXT DEFAULT '',
                      total_reqs  INTEGER DEFAULT 0,
                      vulns_found INTEGER DEFAULT 0
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS results (
                      id              INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_id      INTEGER NOT NULL,
                      timestamp       TEXT,
                      vector_type     TEXT,
                      url             TEXT,
                      parameter       TEXT,
                      category        TEXT,
                      payload         TEXT,
                      status_code     INTEGER,
                      response_time   REAL,
                      response_body   TEXT,
                      response_length INTEGER,
                      vulnerable      INTEGER DEFAULT 0,
                      vuln_type       TEXT DEFAULT '',
                      confidence      TEXT DEFAULT '',
                      FOREIGN KEY (session_id) REFERENCES sessions(id)
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vectors (
                      id          INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_id  INTEGER NOT NULL,
                      vector_type TEXT,
                      url         TEXT,
                      method      TEXT,
                      param_name  TEXT,
                      FOREIGN KEY (session_id) REFERENCES sessions(id)
                    );
                    """
                )

    def create_session(self, target_url: str) -> int:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "INSERT INTO sessions (target_url, started_at) VALUES (?, ?)",
                    (target_url, datetime.now().isoformat()),
                )
                return int(cur.lastrowid)

    def save_result(self, result: ScanResult) -> None:
        try:
            with self._lock:
                with sqlite3.connect(self._db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    conn.execute(
                        """
                        INSERT INTO results (
                            session_id, timestamp, vector_type, url, parameter, category,
                            payload, status_code, response_time, response_body,
                            response_length, vulnerable, vuln_type, confidence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result.session_id,
                            result.timestamp.isoformat(),
                            result.vector_type,
                            result.url,
                            result.parameter,
                            result.category,
                            result.payload,
                            result.status_code,
                            result.response_time_ms,
                            result.response_body,
                            result.response_length,
                            1 if result.vulnerable else 0,
                            result.vuln_type or "",
                            result.confidence or "",
                        ),
                    )
        except Exception:
            return

    def close_session(self, session_id: int, total_reqs: int, vulns_found: int) -> None:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute(
                    "UPDATE sessions SET ended_at=?, total_reqs=?, vulns_found=? WHERE id=?",
                    (datetime.now().isoformat(), total_reqs, vulns_found, session_id),
                )

    def get_all_sessions(self) -> list[SessionRow]:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
        return [
            SessionRow(
                id=row["id"],
                target_url=row["target_url"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                total_reqs=row["total_reqs"],
                vulns_found=row["vulns_found"],
            )
            for row in rows
        ]

    def get_results_for_session(self, session_id: int) -> list[ScanResult]:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM results WHERE session_id=? ORDER BY id ASC",
                    (session_id,),
                ).fetchall()

        results: list[ScanResult] = []
        for row in rows:
            timestamp = datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else datetime.now()
            results.append(
                ScanResult(
                    timestamp=timestamp,
                    session_id=row["session_id"],
                    vector_type=row["vector_type"] or "",
                    url=row["url"] or "",
                    parameter=row["parameter"] or "",
                    category=row["category"] or "",
                    payload=row["payload"] or "",
                    status_code=row["status_code"] or 0,
                    response_time_ms=row["response_time"] or 0.0,
                    response_body=row["response_body"] or "",
                    response_length=row["response_length"] or 0,
                    vulnerable=bool(row["vulnerable"]),
                    vuln_type=row["vuln_type"] or None,
                    confidence=row["confidence"] or None,
                )
            )
        return results

    def export_to_csv(self, session_id: int, filepath: str) -> None:
        results = self.get_results_for_session(session_id)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "session_id",
                    "vector_type",
                    "url",
                    "parameter",
                    "category",
                    "payload",
                    "status_code",
                    "response_time_ms",
                    "response_body",
                    "response_length",
                    "vulnerable",
                    "vuln_type",
                    "confidence",
                ],
            )
            writer.writeheader()
            for r in results:
                writer.writerow(
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "session_id": r.session_id,
                        "vector_type": r.vector_type,
                        "url": r.url,
                        "parameter": r.parameter,
                        "category": r.category,
                        "payload": r.payload,
                        "status_code": r.status_code,
                        "response_time_ms": r.response_time_ms,
                        "response_body": r.response_body,
                        "response_length": r.response_length,
                        "vulnerable": r.vulnerable,
                        "vuln_type": r.vuln_type,
                        "confidence": r.confidence,
                    }
                )

    def export_to_json(self, session_id: int, filepath: str) -> None:
        results = self.get_results_for_session(session_id)
        payload = [
            {
                "timestamp": r.timestamp.isoformat(),
                "session_id": r.session_id,
                "vector_type": r.vector_type,
                "url": r.url,
                "parameter": r.parameter,
                "category": r.category,
                "payload": r.payload,
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "response_body": r.response_body,
                "response_length": r.response_length,
                "vulnerable": r.vulnerable,
                "vuln_type": r.vuln_type,
                "confidence": r.confidence,
            }
            for r in results
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def delete_session(self, session_id: int) -> None:
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("DELETE FROM results WHERE session_id=?", (session_id,))
                conn.execute("DELETE FROM vectors WHERE session_id=?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))

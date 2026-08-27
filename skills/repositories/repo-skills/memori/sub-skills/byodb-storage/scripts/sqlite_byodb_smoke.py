#!/usr/bin/env python3
"""Create and verify a temporary SQLite-backed Memori schema."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from memori import Memori


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "memori.sqlite"
        mem = Memori(conn=lambda: sqlite3.connect(db_path), use_rust_core=False)
        mem.attribution(entity_id="smoke-user", process_id="sqlite-smoke")
        mem.config.storage.build()
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        finally:
            conn.close()
        mem.close()

    print(
        json.dumps(
            {
                "status": "passed",
                "dialect": "sqlite",
                "tables": [row[0] for row in rows],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

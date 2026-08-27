#!/usr/bin/env python3
"""Safe Headroom memory save/search/delete smoke.

By default this script creates a temporary SQLite database, writes one test
memory, searches for it, deletes it, and removes the temporary database. It uses
Headroom's SQLite store plus a deterministic in-script embedder so the smoke does
not contact Qdrant, Neo4j, OpenAI, Hugging Face, or other external services.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SmokeReport:
    ok: bool
    db_path: str
    temporary_db: bool
    user_id: str
    saved_id: str | None = None
    search_hit_count: int = 0
    matched_saved_memory: bool = False
    deleted: bool = False
    post_delete_hit_count: int = 0
    error_type: str | None = None
    error: str | None = None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe local Headroom memory save/search/delete smoke.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=(
            "SQLite memory database to use. Defaults to a temporary database "
            "that is deleted after the smoke."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    return parser.parse_args(argv)


class DeterministicEmbedder:
    """Tiny local embedder for no-network smoke testing.

    It is not a production-quality semantic model. It only proves that
    Headroom's memory orchestration can persist, index, search, and delete a
    memory without relying on model downloads or external services.
    """

    def __init__(self, dimension: int = 32) -> None:
        self._dimension = dimension

    async def embed(self, text: str) -> Any:
        import numpy as np

        vector = np.zeros(self._dimension, dtype=np.float32)
        for token in re.findall(r"\w+", text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            value = int.from_bytes(digest, "big")
            sign = 1.0 if value & 1 else -1.0
            vector[value % self._dimension] += sign
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = (vector / norm).astype(np.float32)
        return vector

    async def embed_batch(self, texts: list[str]) -> list[Any]:
        return [await self.embed(text) for text in texts]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return "deterministic-smoke-embedder"

    @property
    def max_tokens(self) -> int:
        return 256


class InMemoryVectorIndex:
    """Minimal protocol-compatible vector index for the smoke."""

    def __init__(self, dimension: int) -> None:
        self._dimension = dimension
        self._items: dict[str, tuple[Any, Any]] = {}

    async def index(self, memory: Any) -> None:
        if memory.embedding is None:
            raise ValueError("memory has no embedding")
        self._items[memory.id] = (memory.embedding, memory)

    async def index_batch(self, memories: list[Any]) -> int:
        count = 0
        for memory in memories:
            if memory.embedding is not None:
                await self.index(memory)
                count += 1
        return count

    async def remove(self, memory_id: str) -> bool:
        return self._items.pop(memory_id, None) is not None

    async def remove_batch(self, memory_ids: list[str]) -> int:
        count = 0
        for memory_id in memory_ids:
            if await self.remove(memory_id):
                count += 1
        return count

    async def update_embedding(self, memory_id: str, embedding: Any) -> bool:
        if memory_id not in self._items:
            return False
        _old_embedding, memory = self._items[memory_id]
        memory.embedding = embedding
        self._items[memory_id] = (embedding, memory)
        return True

    async def search(self, filter: Any) -> list[Any]:
        import numpy as np
        from headroom.memory.ports import VectorSearchResult

        query = filter.query_vector
        if query is None:
            raise ValueError("query_vector is required for smoke vector search")

        scored: list[tuple[float, Any]] = []
        for vector, memory in self._items.values():
            if filter.user_id is not None and memory.user_id != filter.user_id:
                continue
            if filter.session_id is not None and memory.session_id != filter.session_id:
                continue
            if filter.agent_id is not None and memory.agent_id != filter.agent_id:
                continue
            if filter.scope_levels is not None and memory.scope_level not in filter.scope_levels:
                continue
            if not filter.include_superseded and (
                memory.valid_until is not None or memory.superseded_by is not None
            ):
                continue
            denom = float(np.linalg.norm(query) * np.linalg.norm(vector))
            score = float(np.dot(query, vector) / denom) if denom else 0.0
            if score >= filter.min_similarity:
                scored.append((score, memory))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            VectorSearchResult(memory=memory, similarity=score, rank=rank)
            for rank, (score, memory) in enumerate(scored[: filter.top_k], start=1)
        ]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def size(self) -> int:
        return len(self._items)


async def run_smoke(db_path: Path, *, temporary_db: bool) -> SmokeReport:
    # Import lazily so `--help` works even when Headroom is not installed in the
    # current Python environment.
    from headroom.memory.adapters.fts5 import FTS5TextIndex
    from headroom.memory.adapters.sqlite import SQLiteMemoryStore
    from headroom.memory.core import HierarchicalMemory

    db_path.parent.mkdir(parents=True, exist_ok=True)
    user_id = f"headroom-smoke-{uuid.uuid4().hex[:8]}"
    marker = f"headroom memory smoke marker {uuid.uuid4().hex}"
    content = f"{marker}: user prefers local SQLite memory checks"

    report = SmokeReport(
        ok=False,
        db_path=str(db_path),
        temporary_db=temporary_db,
        user_id=user_id,
    )

    embedder = DeterministicEmbedder()
    memory = HierarchicalMemory(
        store=SQLiteMemoryStore(db_path),
        vector_index=InMemoryVectorIndex(embedder.dimension),
        text_index=FTS5TextIndex(db_path),
        embedder=embedder,
        cache=None,
    )

    try:
        created = await memory.add(
            content=content,
            user_id=user_id,
            importance=0.8,
            metadata={"source": "headroom-memory-smoke"},
        )
        report.saved_id = created.id

        hits = await memory.search(
            "local SQLite memory smoke marker",
            user_id=user_id,
            top_k=5,
        )
        report.search_hit_count = len(hits)
        report.matched_saved_memory = any(
            hit.memory.id == created.id or marker in hit.memory.content for hit in hits
        )

        report.deleted = bool(await memory.delete(created.id))

        post_delete_hits = await memory.search(
            "local SQLite memory smoke marker",
            user_id=user_id,
            top_k=5,
        )
        report.post_delete_hit_count = sum(
            1
            for hit in post_delete_hits
            if hit.memory.id == created.id or marker in hit.memory.content
        )

        report.ok = bool(
            report.saved_id
            and report.search_hit_count >= 1
            and report.matched_saved_memory
            and report.deleted
            and report.post_delete_hit_count == 0
        )
        return report
    finally:
        await memory.close()


def print_human(report: SmokeReport) -> None:
    status = "PASS" if report.ok else "FAIL"
    print(f"Headroom memory smoke: {status}")
    print(f"  database: {'temporary' if report.temporary_db else 'explicit'}")
    print(f"  db path: {report.db_path}")
    print(f"  user id: {report.user_id}")
    if report.saved_id:
        print(f"  saved id: {report.saved_id}")
    print(f"  search hits: {report.search_hit_count}")
    print(f"  matched saved memory: {report.matched_saved_memory}")
    print(f"  deleted: {report.deleted}")
    print(f"  post-delete matching hits: {report.post_delete_hit_count}")
    if report.error:
        print(f"  error: {report.error_type}: {report.error}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))

    tempdir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.db_path is None:
            tempdir = tempfile.TemporaryDirectory(prefix="headroom-memory-smoke-")
            db_path = Path(tempdir.name) / "memory.db"
            temporary_db = True
        else:
            db_path = args.db_path.expanduser().resolve(strict=False)
            temporary_db = False

        try:
            report = asyncio.run(run_smoke(db_path, temporary_db=temporary_db))
        except Exception as exc:  # noqa: BLE001 - CLI smoke should report all failures.
            report = SmokeReport(
                ok=False,
                db_path=str(db_path),
                temporary_db=temporary_db,
                user_id="uninitialized",
                error_type=type(exc).__name__,
                error=str(exc),
            )

        if args.json:
            print(json.dumps(asdict(report), indent=2, sort_keys=True))
        else:
            print_human(report)
        return 0 if report.ok else 1
    finally:
        if tempdir is not None:
            tempdir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())

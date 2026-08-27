#!/usr/bin/env python3
"""Demonstrate offline GraphRAG factory registration patterns.

This script registers small in-memory Storage, Cache, InputReader, and VectorStore
implementations. It avoids external services and is intended as a copy/adapt
reference for custom provider work.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import re
from datetime import datetime, timezone
from typing import Any


def _load_graphrag_symbols() -> dict[str, Any]:
    try:
        from graphrag_cache import Cache, CacheConfig, create_cache, register_cache
        from graphrag_input import InputConfig, InputReader, TextDocument, create_input_reader
        from graphrag_input.input_reader_factory import register_input_reader
        from graphrag_storage import Storage, StorageConfig, create_storage, register_storage
        from graphrag_vectors import IndexSchema, VectorStoreConfig
        from graphrag_vectors import create_vector_store, register_vector_store
        from graphrag_vectors import VectorStore, VectorStoreDocument, VectorStoreSearchResult
    except ImportError as exc:
        raise SystemExit(
            "GraphRAG packages are not importable. Install GraphRAG before running "
            "this demonstration, or use --help to inspect options."
        ) from exc

    return {
        "Cache": Cache,
        "CacheConfig": CacheConfig,
        "create_cache": create_cache,
        "register_cache": register_cache,
        "InputConfig": InputConfig,
        "InputReader": InputReader,
        "TextDocument": TextDocument,
        "create_input_reader": create_input_reader,
        "register_input_reader": register_input_reader,
        "Storage": Storage,
        "StorageConfig": StorageConfig,
        "create_storage": create_storage,
        "register_storage": register_storage,
        "IndexSchema": IndexSchema,
        "VectorStoreConfig": VectorStoreConfig,
        "create_vector_store": create_vector_store,
        "register_vector_store": register_vector_store,
        "VectorStore": VectorStore,
        "VectorStoreDocument": VectorStoreDocument,
        "VectorStoreSearchResult": VectorStoreSearchResult,
    }


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def build_classes(symbols: dict[str, Any]) -> dict[str, Any]:
    Storage = symbols["Storage"]
    Cache = symbols["Cache"]
    InputReader = symbols["InputReader"]
    TextDocument = symbols["TextDocument"]
    VectorStore = symbols["VectorStore"]
    VectorStoreSearchResult = symbols["VectorStoreSearchResult"]

    class DemoStorage(Storage):
        def __init__(self, prefix: str = "", seed: dict[str, str] | None = None, **kwargs: Any) -> None:
            self.prefix = prefix.strip("/")
            self._items = dict(seed or {"input/a.txt": "alpha", "input/b.txt": "beta"})
            self._created = {
                key: datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat()
                for key in self._items
            }

        def _key(self, key: str) -> str:
            clean = key.strip("/")
            return f"{self.prefix}/{clean}" if self.prefix else clean

        def find(self, file_pattern: re.Pattern[str]):
            for key in sorted(self._items):
                if file_pattern.search(key):
                    yield key

        async def get(self, key: str, as_bytes: bool | None = None, encoding: str | None = None) -> Any:
            value = self._items[self._key(key)]
            return value.encode(encoding or "utf-8") if as_bytes else value

        async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
            full_key = self._key(key)
            self._items[full_key] = value.decode(encoding or "utf-8") if isinstance(value, bytes) else value
            self._created.setdefault(full_key, datetime.now(timezone.utc).isoformat())

        async def has(self, key: str) -> bool:
            return self._key(key) in self._items

        async def delete(self, key: str) -> None:
            self._items.pop(self._key(key), None)

        async def clear(self) -> None:
            self._items.clear()

        def child(self, name: str | None) -> "DemoStorage":
            child_prefix = "/".join(part for part in [self.prefix, name or ""] if part)
            child = DemoStorage(prefix=child_prefix)
            child._items = self._items
            child._created = self._created
            return child

        def keys(self) -> list[str]:
            return sorted(self._items)

        async def get_creation_date(self, key: str) -> str:
            return self._created[self._key(key)]

    class DemoCache(Cache):
        def __init__(self, *, storage: Any | None = None, namespace: str = "root", **kwargs: Any) -> None:
            self.storage = storage
            self.namespace = namespace
            self._values: dict[str, Any] = {}

        def _key(self, key: str) -> str:
            return f"{self.namespace}:{key}"

        async def get(self, key: str) -> Any:
            return self._values.get(self._key(key))

        async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
            self._values[self._key(key)] = value

        async def has(self, key: str) -> bool:
            return self._key(key) in self._values

        async def delete(self, key: str) -> None:
            self._values.pop(self._key(key), None)

        async def clear(self) -> None:
            self._values.clear()

        def child(self, name: str) -> "DemoCache":
            child = DemoCache(storage=self.storage, namespace=f"{self.namespace}/{name}")
            child._values = self._values
            return child

    class DemoInputReader(InputReader):
        async def read_file(self, path: str) -> list[Any]:
            text = await self._storage.get(path, encoding=self._encoding)
            return [TextDocument(id=path, text=text, title=path, creation_date="2024-01-01")]

    class OfflineVectorStore(VectorStore):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._documents: dict[str, Any] = {}
            self.connected = False

        def connect(self) -> None:
            self.connected = True

        def create_index(self) -> None:
            self.connected = True

        def load_documents(self, documents: list[Any]) -> None:
            for document in documents:
                self._prepare_document(document)
                self._documents[str(document.id)] = document

        def similarity_search_by_vector(
            self,
            query_embedding: list[float],
            k: int = 10,
            select: list[str] | None = None,
            filters: Any | None = None,
            include_vectors: bool = True,
        ) -> list[Any]:
            candidates = list(self._documents.values())
            if filters is not None:
                candidates = [doc for doc in candidates if filters.evaluate(doc)]
            scored = [
                VectorStoreSearchResult(document=doc, score=_cosine(query_embedding, doc.vector or []))
                for doc in candidates
            ]
            scored.sort(key=lambda item: item.score, reverse=True)
            if select is not None or not include_vectors:
                for result in scored:
                    if select is not None:
                        result.document.data = {key: result.document.data[key] for key in select if key in result.document.data}
                    if not include_vectors:
                        result.document.vector = None
            return scored[:k]

        def search_by_id(self, id: str, select: list[str] | None = None, include_vectors: bool = True) -> Any:
            document = self._documents[str(id)]
            if select is not None:
                document.data = {key: document.data[key] for key in select if key in document.data}
            if not include_vectors:
                document.vector = None
            return document

        def count(self) -> int:
            return len(self._documents)

        def remove(self, ids: list[str]) -> None:
            for id_value in ids:
                self._documents.pop(str(id_value), None)

        def update(self, document: Any) -> None:
            self._prepare_update(document)
            self._documents[str(document.id)] = document

    return {
        "DemoStorage": DemoStorage,
        "DemoCache": DemoCache,
        "DemoInputReader": DemoInputReader,
        "OfflineVectorStore": OfflineVectorStore,
    }


async def run_demo() -> None:
    symbols = _load_graphrag_symbols()
    classes = build_classes(symbols)

    symbols["register_storage"]("demo-memory-storage", classes["DemoStorage"], scope="transient")
    symbols["register_cache"]("demo-cache", classes["DemoCache"], scope="transient")
    symbols["register_input_reader"]("demo-input", classes["DemoInputReader"], scope="transient")
    symbols["register_vector_store"]("demo-vector", classes["OfflineVectorStore"], scope="transient")

    storage = symbols["create_storage"](symbols["StorageConfig"](type="demo-memory-storage"))
    cache = symbols["create_cache"](symbols["CacheConfig"](type="demo-cache", namespace="example"), storage=storage)
    await cache.set("answer", {"ok": True})

    reader = symbols["create_input_reader"](
        symbols["InputConfig"](type="demo-input", file_pattern=r"input/.*\.txt$"),
        storage,
    )
    documents = await reader.read_files()

    store = symbols["create_vector_store"](
        symbols["VectorStoreConfig"](type="demo-vector", fields={"published_at": "date", "kind": "str"}),
        symbols["IndexSchema"](index_name="demo", vector_size=3),
    )
    store.load_documents([
        symbols["VectorStoreDocument"](
            id="a",
            vector=[1.0, 0.0, 0.0],
            data={"kind": "note", "published_at": "2024-03-15T08:00:00"},
        ),
        symbols["VectorStoreDocument"](
            id="b",
            vector=[0.0, 1.0, 0.0],
            data={"kind": "memo", "published_at": "2024-04-01T08:00:00"},
        ),
    ])

    print("registered storage keys:", storage.keys())
    print("cache has answer:", await cache.has("answer"))
    print("input documents:", [doc.id for doc in documents])
    print("vector count:", store.count())
    print("best vector id:", store.similarity_search_by_vector([1.0, 0.0, 0.0], k=1)[0].document.id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register and exercise offline GraphRAG mock extensions.")
    parser.add_argument("--demo", action="store_true", help="Run the registration demo and print summary checks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.demo:
        asyncio.run(run_demo())
    else:
        print("Use --demo to register and exercise offline mock extensions.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Smoke-test nano-graphrag storage backends without provider API calls.

The script uses a deterministic fake embedding function and a temporary working
directory by default. It validates basic NetworkX graph persistence plus local
NanoVectorDB/HNSW vector upsert/query behavior. No LLM or embedding provider is
called.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


def make_fake_embedding(embedding_dim: int, max_token_size: int = 8192):
    from nano_graphrag._utils import wrap_embedding_func_with_attrs

    @wrap_embedding_func_with_attrs(
        embedding_dim=embedding_dim,
        max_token_size=max_token_size,
    )
    async def fake_embedding(texts: list[str]) -> np.ndarray:
        rows = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values = np.array(
                [((digest[i % len(digest)] + 31 * i) % 251) / 250.0 for i in range(embedding_dim)],
                dtype=np.float32,
            )
            norm = np.linalg.norm(values)
            rows.append(values / norm if norm else values)
        return np.vstack(rows).astype(np.float32)

    return fake_embedding


def make_global_config(working_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "working_dir": str(working_dir),
        "embedding_batch_num": args.embedding_batch_num,
        "query_better_than_threshold": args.query_threshold,
        "vector_db_storage_cls_kwargs": {
            "ef_construction": args.ef_construction,
            "M": args.hnsw_m,
            "max_elements": args.max_elements,
            "ef_search": args.ef_search,
            "num_threads": args.num_threads,
        },
        "max_graph_cluster_size": 10,
        "graph_cluster_seed": 0xDEADBEEF,
        "node2vec_params": {
            "dimensions": args.embedding_dim,
            "num_walks": 2,
            "walk_length": 4,
            "window_size": 2,
            "iterations": 1,
            "random_seed": 3,
        },
    }


async def smoke_networkx(working_dir: Path, config: dict[str, Any], namespace_prefix: str) -> dict[str, Any]:
    from nano_graphrag._storage import NetworkXStorage

    namespace = f"{namespace_prefix}_graph"
    storage = NetworkXStorage(namespace=namespace, global_config=config)
    await storage.upsert_node("ALPHA", {"entity_type": "CONCEPT", "description": "Alpha node", "source_id": "chunk-alpha"})
    await storage.upsert_node("BETA", {"entity_type": "CONCEPT", "description": "Beta node", "source_id": "chunk-beta"})
    await storage.upsert_edge("ALPHA", "BETA", {"weight": 1.0, "description": "Alpha connects to beta", "source_id": "chunk-alpha"})

    checks = {
        "has_alpha": await storage.has_node("ALPHA"),
        "has_edge": await storage.has_edge("ALPHA", "BETA"),
        "alpha_degree": await storage.node_degree("ALPHA"),
        "edge": await storage.get_edge("ALPHA", "BETA"),
    }
    assert checks["has_alpha"] is True
    assert checks["has_edge"] is True
    assert checks["alpha_degree"] == 1
    assert checks["edge"] is not None and float(checks["edge"].get("weight", 0)) == 1.0

    await storage.index_done_callback()
    graphml_path = working_dir / f"graph_{namespace}.graphml"
    assert graphml_path.exists(), f"Expected GraphML artifact missing: {graphml_path}"

    reloaded = NetworkXStorage(namespace=namespace, global_config=config)
    assert await reloaded.has_node("ALPHA") is True
    assert await reloaded.has_edge("ALPHA", "BETA") is True

    return {
        "backend": "networkx",
        "status": "ok",
        "graphml": graphml_path.name,
        "nodes": 2,
        "edges": 1,
    }


async def smoke_nanovectordb(config: dict[str, Any], embedding_func, namespace_prefix: str) -> dict[str, Any]:
    from nano_graphrag._storage import NanoVectorDBStorage

    namespace = f"{namespace_prefix}_entities"
    storage = NanoVectorDBStorage(
        namespace=namespace,
        global_config=config,
        embedding_func=embedding_func,
        meta_fields={"entity_name"},
    )
    await storage.upsert(
        {
            "entity-alpha": {"content": "alpha graph storage", "entity_name": "ALPHA"},
            "entity-beta": {"content": "beta vector storage", "entity_name": "BETA"},
        }
    )
    results = await storage.query("alpha graph storage", top_k=2)
    assert results, "NanoVectorDB returned no results"
    assert "id" in results[0], "NanoVectorDB result missing id"
    assert "distance" in results[0], "NanoVectorDB result missing distance"
    assert any("entity_name" in result for result in results), "NanoVectorDB result missing entity_name metadata"
    await storage.index_done_callback()

    return {
        "backend": "nanovectordb",
        "status": "ok",
        "result_count": len(results),
        "result_keys": sorted(str(k) for k in results[0].keys()),
        "artifact": f"vdb_{namespace}.json",
    }


async def smoke_hnsw(config: dict[str, Any], embedding_func, namespace_prefix: str) -> dict[str, Any]:
    from nano_graphrag._storage import HNSWVectorStorage

    namespace = f"{namespace_prefix}_hnsw_entities"
    storage = HNSWVectorStorage(
        namespace=namespace,
        global_config=config,
        embedding_func=embedding_func,
        meta_fields={"entity_name"},
    )
    await storage.upsert(
        {
            "entity-alpha": {"content": "alpha hnsw storage", "entity_name": "ALPHA"},
            "entity-beta": {"content": "beta hnsw storage", "entity_name": "BETA"},
            "entity-gamma": {"content": "gamma hnsw storage", "entity_name": "GAMMA"},
        }
    )
    results = await storage.query("alpha hnsw storage", top_k=2)
    assert results, "HNSW returned no results"
    assert "id" in results[0], "HNSW result missing id"
    assert "distance" in results[0], "HNSW result missing distance"
    assert "similarity" in results[0], "HNSW result missing similarity"
    await storage.index_done_callback()

    return {
        "backend": "hnsw",
        "status": "ok",
        "result_count": len(results),
        "result_keys": sorted(str(k) for k in results[0].keys()),
        "artifacts": [f"{namespace}_hnsw.index", f"{namespace}_hnsw_metadata.pkl"],
    }


async def run_smokes(args: argparse.Namespace, working_dir: Path) -> list[dict[str, Any]]:
    embedding_func = make_fake_embedding(args.embedding_dim)
    config = make_global_config(working_dir, args)
    backends = [item.strip().lower() for item in args.backends.split(",") if item.strip()]
    if "all" in backends:
        backends = ["networkx", "nanovectordb", "hnsw"]

    results: list[dict[str, Any]] = []
    for backend in backends:
        if backend == "networkx":
            results.append(await smoke_networkx(working_dir, config, args.namespace_prefix))
        elif backend == "nanovectordb":
            results.append(await smoke_nanovectordb(config, embedding_func, args.namespace_prefix))
        elif backend == "hnsw":
            results.append(await smoke_hnsw(config, embedding_func, args.namespace_prefix))
        else:
            raise ValueError(f"Unsupported backend in --backends: {backend}")
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely instantiate nano-graphrag NetworkX, NanoVectorDB, and HNSW storage with fake embeddings.",
    )
    parser.add_argument(
        "--backends",
        default="all",
        help="Comma-separated backends to run: all, networkx, nanovectordb, hnsw. Default: all.",
    )
    parser.add_argument("--working-dir", type=Path, help="Directory for temporary artifacts. Defaults to a disposable temp directory.")
    parser.add_argument("--keep-working-dir", action="store_true", help="Keep the auto-created temp working directory after the smoke.")
    parser.add_argument("--namespace-prefix", default="storage_smoke", help="Namespace prefix to avoid collisions. Default: storage_smoke.")
    parser.add_argument("--embedding-dim", type=int, default=16, help="Fake embedding dimension. Default: 16.")
    parser.add_argument("--embedding-batch-num", type=int, default=4, help="Embedding batch size in global config. Default: 4.")
    parser.add_argument("--query-threshold", type=float, default=0.0, help="NanoVectorDB query threshold for smoke. Default: 0.0.")
    parser.add_argument("--max-elements", type=int, default=32, help="HNSW max_elements. Default: 32.")
    parser.add_argument("--ef-search", type=int, default=10, help="HNSW ef_search. Default: 10.")
    parser.add_argument("--ef-construction", type=int, default=40, help="HNSW ef_construction. Default: 40.")
    parser.add_argument("--hnsw-m", type=int, default=8, help="HNSW M parameter. Default: 8.")
    parser.add_argument("--num-threads", type=int, default=-1, help="HNSW num_threads. Default: -1.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    return parser


def format_text(results: list[dict[str, Any]], working_dir: Path, kept: bool) -> str:
    lines = [f"storage_smoke working_dir={working_dir} kept={kept}"]
    for result in results:
        lines.append(f"- {result['backend']}: {result['status']}")
        for key, value in result.items():
            if key in {"backend", "status"}:
                continue
            lines.append(f"    {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.embedding_dim <= 0:
        parser.error("--embedding-dim must be positive")
    if args.max_elements < 3 and ("hnsw" in args.backends or "all" in args.backends):
        parser.error("--max-elements must be at least 3 for the default HNSW smoke data")

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.working_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="nano_graphrag_storage_smoke_")
        working_dir = Path(temp_dir.name)
    else:
        working_dir = args.working_dir.expanduser()
        working_dir.mkdir(parents=True, exist_ok=True)

    kept = bool(args.working_dir or args.keep_working_dir)
    try:
        results = asyncio.run(run_smokes(args, working_dir))
        payload = {"working_dir": str(working_dir), "kept": kept, "results": results}
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(format_text(results, working_dir, kept))
        if temp_dir is not None and args.keep_working_dir:
            # TemporaryDirectory cannot be detached, so copy to a stable sibling before cleanup.
            keep_path = Path(tempfile.mkdtemp(prefix="nano_graphrag_storage_smoke_keep_"))
            shutil.copytree(working_dir, keep_path, dirs_exist_ok=True)
            print(f"Copied temp artifacts to: {keep_path}")
        return 0
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        print(f"Missing Python dependency while importing/running storage smoke: {missing}", file=sys.stderr)
        print("Install the package dependency or choose a backend whose imports are available.", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Storage smoke failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))

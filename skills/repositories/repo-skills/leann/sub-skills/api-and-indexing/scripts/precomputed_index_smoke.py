#!/usr/bin/env python3
"""Build and validate a tiny LEANN index without model downloads or credentials.

The fixture uses deterministic precomputed vectors and HNSW with stored vectors.
Its search check is pure SQLite FTS5 BM25, so it never computes a query embedding.
By default all artifacts are created in a temporary directory and removed after
the check. Pass --output-dir to retain a new, previously nonexistent directory.
"""

from __future__ import annotations

import argparse
import json
import pickle
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Retain artifacts in this new directory. The path must not already "
            "exist; parent directories are created safely."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable success summary instead of prose.",
    )
    return parser.parse_args(argv)


def fail(message: str, *, code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return code


def prepare_work_dir(output_dir: Path | None) -> tuple[Path, bool]:
    if output_dir is None:
        return Path(tempfile.mkdtemp(prefix="leann-precomputed-smoke-")), True

    target = output_dir.expanduser()
    if target.exists():
        raise ValueError(f"--output-dir already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    return target, False


def validate_passages(base_path: Path, expected_ids: list[str]) -> dict[str, Any]:
    meta_path = Path(f"{base_path}.meta.json")
    passages_path = Path(f"{base_path}.passages.jsonl")
    offsets_path = Path(f"{base_path}.passages.idx")
    primary_index_path = base_path.parent / f"{base_path.stem}.index"

    required = [meta_path, passages_path, offsets_path, primary_index_path]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise AssertionError(f"missing required artifacts: {', '.join(missing)}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("backend_name") != "hnsw":
        raise AssertionError(f"unexpected backend: {meta.get('backend_name')!r}")
    if meta.get("dimensions") != 4:
        raise AssertionError(f"unexpected dimensions: {meta.get('dimensions')!r}")
    if meta.get("built_from_precomputed_embeddings") is not True:
        raise AssertionError("metadata does not record precomputed embeddings")

    rows = []
    for line_number, line in enumerate(passages_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"invalid passage JSON on line {line_number}: {exc}") from exc

    row_ids = [row.get("id") for row in rows]
    if row_ids != expected_ids:
        raise AssertionError(f"passage IDs are not aligned: {row_ids!r}")
    if len(set(row_ids)) != len(row_ids):
        raise AssertionError("passage IDs are not unique")

    # The generated offset map is a trusted artifact created in this process.
    with offsets_path.open("rb") as stream:
        offsets = pickle.load(stream)
    if set(offsets) != set(expected_ids):
        raise AssertionError("offset-map IDs do not match passage IDs")

    with passages_path.open(encoding="utf-8") as stream:
        for passage_id, offset in offsets.items():
            stream.seek(offset)
            row = json.loads(stream.readline())
            if row.get("id") != passage_id:
                raise AssertionError(f"offset for {passage_id!r} resolves to another row")

    return {"meta": meta, "rows": rows, "required": required}


def run_smoke(work_dir: Path) -> dict[str, Any]:
    try:
        import numpy as np
        from leann import LeannBuilder, LeannSearcher
        from leann.api import get_registered_backends
    except ImportError as exc:
        dependency = getattr(exc, "name", None) or str(exc)
        raise RuntimeError(
            f"missing or unloadable Python dependency {dependency!r}; "
            "install LEANN with its HNSW backend and NumPy"
        ) from exc

    if "hnsw" not in get_registered_backends():
        raise RuntimeError(
            "the HNSW backend is not registered; install the LEANN HNSW backend before running this smoke"
        )

    ids = ["fruit", "code", "weather"]
    passages = [
        (
            "Orchard release note for the apple harvest.",
            {"id": "fruit", "kind": "note", "year": 2025, "attrs": {"tier": "gold"}},
        ),
        (
            "Compiler reference for deterministic build flags.",
            {"id": "code", "kind": "manual", "year": "2024", "attrs": {"tier": "silver"}},
        ),
        (
            "Weather bulletin with rain expected tomorrow.",
            {"id": "weather", "kind": "bulletin", "active": True},
        ),
    ]
    embeddings = np.ascontiguousarray(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    if embeddings.shape != (len(ids), 4):
        raise AssertionError(f"unexpected fixture shape: {embeddings.shape!r}")

    base_path = work_dir / "documents.leann"
    builder = LeannBuilder(
        backend_name="hnsw",
        embedding_model="offline-precomputed-fixture",
        dimensions=4,
        embedding_mode="sentence-transformers",
        prebuild_bm25=False,
        is_recompute=False,
        is_compact=False,
    )
    for passage_id, (text, metadata) in zip(ids, passages, strict=True):
        if metadata.get("id") != passage_id:
            raise AssertionError("fixture passage/vector IDs are misaligned")
        builder.add_text(text, metadata)
    builder.build_index_from_arrays(str(base_path), ids, embeddings)

    validated = validate_passages(base_path, ids)

    try:
        with LeannSearcher(
            str(base_path),
            enable_warmup=False,
            recompute_embeddings=False,
            use_daemon=False,
        ) as searcher:
            results = searcher.search(
                "orchard",
                top_k=3,
                vector_weight=0.0,
                metadata_filters={
                    "kind": {"==": "note"},
                    "year": {">=": 2024},
                },
            )
    except Exception as exc:
        if "fts5" in str(exc).lower() or "bm25" in str(exc).lower():
            raise RuntimeError(
                "pure-BM25 validation failed; the runtime needs SQLite FTS5 and a writable output directory"
            ) from exc
        raise

    if len(results) != 1 or results[0].id != "fruit":
        result_view = [(result.id, result.score) for result in results]
        raise AssertionError(f"unexpected filtered BM25 results: {result_view!r}")
    if results[0].metadata.get("attrs", {}).get("tier") != "gold":
        raise AssertionError("nested metadata did not survive the passage round trip")

    bm25_path = work_dir / "documents.leann.bm25.sqlite"
    if not bm25_path.is_file():
        raise AssertionError("on-demand BM25 database was not created")

    return {
        "status": "ok",
        "backend": "hnsw",
        "dimensions": validated["meta"]["dimensions"],
        "passages": len(validated["rows"]),
        "result_ids": [result.id for result in results],
        "artifact_names": sorted(path.name for path in work_dir.iterdir() if path.is_file()),
        "output_dir": str(work_dir),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    work_dir: Path | None = None
    remove_after = False
    try:
        work_dir, remove_after = prepare_work_dir(args.output_dir)
        summary = run_smoke(work_dir)
        if remove_after:
            summary["output_dir"] = "temporary (removed after validation)"
        if args.json:
            print(json.dumps(summary, sort_keys=True))
        else:
            print("LEANN precomputed-index smoke: OK")
            print(f"  backend: {summary['backend']}")
            print(f"  dimensions: {summary['dimensions']}")
            print(f"  passages: {summary['passages']}")
            print(f"  filtered BM25 result IDs: {', '.join(summary['result_ids'])}")
            print(f"  artifacts: {', '.join(summary['artifact_names'])}")
            print(f"  output: {summary['output_dir']}")
        return 0
    except (AssertionError, ImportError, RuntimeError, ValueError, OSError) as exc:
        return fail(str(exc))
    except KeyboardInterrupt:
        return fail("interrupted", code=130)
    finally:
        if remove_after and work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

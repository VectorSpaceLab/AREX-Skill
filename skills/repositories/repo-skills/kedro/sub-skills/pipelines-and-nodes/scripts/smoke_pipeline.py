#!/usr/bin/env python3
"""Build and optionally run a tiny Kedro pipeline.

This script is self-contained and uses only public Kedro package imports.
It imports public Kedro APIs, builds a small graph from pure functions, validates
namespaced pipeline reuse, and uses DataCatalog plus SequentialRunner when those
runtime surfaces are available.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test Kedro node/pipeline APIs with a tiny in-memory graph. "
            "Use --graph-only when catalog or runner dependencies are unavailable."
        )
    )
    parser.add_argument(
        "--graph-only",
        action="store_true",
        help="Only build and inspect the graph; skip DataCatalog and SequentialRunner execution.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a compact JSON summary instead of human-readable lines.",
    )
    return parser.parse_args()


def read_raw(raw: str) -> str:
    return raw.strip()


def add_suffix(clean_text: str, suffix: str) -> str:
    return f"{clean_text}{suffix}"


def build_pipeline() -> Any:
    from kedro.pipeline import node, pipeline

    base_pipeline = pipeline(
        [
            node(read_raw, "raw_text", "clean_text", name="read_raw", tags="prep"),
            node(
                add_suffix,
                ["clean_text", "params:suffix"],
                "final_text",
                name="add_suffix",
                tags=["prep", "features"],
            ),
        ]
    )

    return pipeline(
        base_pipeline,
        inputs={"raw_text": "example_raw_text"},
        outputs={"final_text": "example_final_text"},
        parameters={"suffix": "example_suffix"},
        namespace="example",
    )


def graph_summary(pipe: Any) -> dict[str, Any]:
    grouped = pipe.group_nodes_by(group_by="namespace")
    return {
        "inputs": sorted(pipe.inputs()),
        "outputs": sorted(pipe.outputs()),
        "datasets": sorted(pipe.datasets()),
        "nodes": [node.name for node in pipe.nodes],
        "tags": {node.name: sorted(node.tags) for node in pipe.nodes},
        "groups": [
            {
                "name": group.name,
                "type": group.type,
                "nodes": group.nodes,
                "dependencies": group.dependencies,
            }
            for group in grouped
        ],
    }


def run_pipeline(pipe: Any) -> Any:
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    catalog = DataCatalog(
        datasets={
            "example_raw_text": MemoryDataset(data="kedro"),
            "params:example_suffix": MemoryDataset(data="-pass"),
        }
    )
    result = SequentialRunner().run(pipe, catalog)
    return result["example_final_text"].load()


def main() -> int:
    args = parse_args()

    try:
        import kedro

        pipe = build_pipeline()
        summary = graph_summary(pipe)
        run_output = None

        if not args.graph_only:
            run_output = run_pipeline(pipe)
            if run_output != "kedro-pass":
                raise RuntimeError(f"Unexpected pipeline output: {run_output!r}")

        payload = {
            "status": "PASS",
            "kedro_version": kedro.__version__,
            "graph": summary,
            "output": run_output,
        }

        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"PASS Kedro {kedro.__version__}")
            print("nodes:", ", ".join(summary["nodes"]))
            print("inputs:", ", ".join(summary["inputs"]))
            print("outputs:", ", ".join(summary["outputs"]))
            if run_output is not None:
                print("output:", run_output)
            else:
                print("output: skipped (--graph-only)")
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any failure clearly.
        message = f"FAIL {type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps({"status": "FAIL", "error": message}, sort_keys=True))
        else:
            print(message, file=sys.stderr)
            print(
                "Hint: verify that the public 'kedro' package is installed in this Python environment. "
                "If only graph APIs are available, retry with --graph-only.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

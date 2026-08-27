#!/usr/bin/env python3
"""Check ColBERT package imports, versions, backend visibility, and key API signatures.

This script is safe by default: it does not load checkpoints, download models,
start servers, build indexes, or run retrieval.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
from typing import Any


def try_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "module": name, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ColBERT imports, backend facts, and public API signatures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a text summary.")
    parser.add_argument("--include-optional", action="store_true", help="Also inspect optional utility and Baleen imports.")
    args = parser.parse_args()

    modules = ["colbert", "colbert.infra", "colbert.data", "colbert.modeling.checkpoint"]
    if args.include_optional:
        modules.extend(["utility", "baleen"])

    report: dict[str, Any] = {
        "distributions": {name: dist_version(name) for name in ["colbert-ai", "torch", "faiss-cpu", "faiss-gpu", "transformers"]},
        "imports": [try_import(name) for name in modules],
        "torch": {},
        "signatures": {},
    }

    try:
        import torch

        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_build": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        from colbert import IndexUpdater, Indexer, Searcher, Trainer
        from colbert.data import Collection, Queries, Ranking
        from colbert.infra import ColBERTConfig, Run, RunConfig

        for obj in [Indexer, Searcher, Trainer, IndexUpdater, Run, RunConfig, ColBERTConfig, Collection, Queries, Ranking]:
            report["signatures"][obj.__name__] = str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["signature_error"] = f"{type(exc).__name__}: {exc}"

    failed_imports = [item for item in report["imports"] if not item["ok"]]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ColBERT environment check")
        print("Distributions:")
        for name, version in report["distributions"].items():
            print(f"  {name}: {version or 'not installed'}")
        print("Imports:")
        for item in report["imports"]:
            status = "ok" if item["ok"] else item["error"]
            print(f"  {item['module']}: {status}")
        print("Torch:", report["torch"])
        if report["signatures"]:
            print("Verified signatures:")
            for name, signature in report["signatures"].items():
                print(f"  {name}{signature}")
        if failed_imports:
            print("One or more imports failed; install the missing extras/backends and rerun this script.")

    return 1 if failed_imports or "signature_error" in report else 0


if __name__ == "__main__":
    raise SystemExit(main())

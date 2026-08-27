#!/usr/bin/env python3
"""Inspect the installed giskard.scan public surface without running scans.

Purpose:
    Print installed package versions, important giskard.scan signatures,
    built-in scan item names, a tiny KnowledgeBase.from_texts smoke check, and
    optional third-party scanner availability.

Safety:
    This script does not call vulnerability_scan, quality_scan,
    third_party_scan, live LLM providers, embedding providers, remote datasets,
    or user targets. It is safe to run from any current working directory.

Example:
    python scripts/inspect_scan_api.py
"""

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import inspect
import os
import sys
from collections.abc import Callable
from typing import Any

# Avoid telemetry side effects during a diagnostic import.
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")


def _version(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "not installed"


def _has_module(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


def _signature(obj: Callable[..., Any]) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<signature unavailable: {exc}>"


def _print_items(label: str, items: list[str], limit: int = 12) -> None:
    print(f"{label}: {len(items)} item(s)")
    if items:
        shown = ", ".join(items[:limit])
        suffix = "" if len(items) <= limit else f", ... (+{len(items) - limit} more)"
        print(f"  {shown}{suffix}")


def main() -> int:
    try:
        import giskard.scan as scan
        from giskard.scan import Document, KnowledgeBase, list_scan_items
    except Exception as exc:  # noqa: BLE001 - diagnostic CLI should report any import failure.
        print("giskard.scan import: FAILED", file=sys.stderr)
        print(f"  {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Install scan support first, for example: pip install 'giskard[scan]' "
            "or pip install giskard-scan",
            file=sys.stderr,
        )
        return 2

    print("giskard.scan import: ok")
    print("versions:")
    for dist in ("giskard", "giskard-scan", "giskard-checks", "giskard-agents", "giskard-llm"):
        print(f"  {dist}: {_version(dist)}")
    print(f"  giskard.scan.__version__: {getattr(scan, '__version__', 'unknown')}")
    print(f"DEFAULT_TARGET_MODE: {getattr(scan, 'DEFAULT_TARGET_MODE', 'unknown')}")

    print("\npublic signatures:")
    for name in ("generate_suite", "vulnerability_scan", "quality_scan", "list_scan_items", "third_party_scan"):
        obj = getattr(scan, name, None)
        if obj is None:
            print(f"  {name}: missing")
        else:
            print(f"  {name}{_signature(obj)}")
    print(f"  Document{_signature(Document)}")
    print(f"  KnowledgeBase{_signature(KnowledgeBase)}")

    print("\nknowledge base smoke:")
    kb = KnowledgeBase.from_texts(["A tiny local document for API inspection."])
    print(f"  documents: {len(kb.documents)}")
    print(f"  first content: {kb.documents[0].content!r}")
    print(f"  embeddings computed: {kb.documents[0].embeddings is not None}")

    print("\nscan items:")
    try:
        _print_items('  list_scan_items("giskard")', list_scan_items("giskard"))
    except Exception as exc:  # noqa: BLE001 - keep optional diagnostics actionable.
        print(f'  list_scan_items("giskard"): failed ({type(exc).__name__}: {exc})')

    print("\noptional scanner availability:")
    optional_modules = {
        "garak": ("garak", "garak._plugins"),
        "deepteam": ("deepteam", "deepteam.vulnerabilities"),
        "lidar": ("lidar",),
    }
    for tool, modules in optional_modules.items():
        status = ", ".join(f"{module}={'yes' if _has_module(module) else 'no'}" for module in modules)
        print(f"  {tool}: {status}")

    for tool in ("garak", "deepteam"):
        try:
            _print_items(f'  list_scan_items("{tool}")', list_scan_items(tool), limit=8)
        except ImportError as exc:
            print(f'  list_scan_items("{tool}"): optional dependency missing ({exc})')
        except Exception as exc:  # noqa: BLE001 - scanner imports can fail for many optional reasons.
            print(f'  list_scan_items("{tool}"): unavailable ({type(exc).__name__}: {exc})')

    print('  list_scan_items("lidar"): not a public listing API; use third_party_scan(tool="lidar") only when private lidar is installed')
    print("\nNo scans, providers, targets, embeddings, or remote dataset downloads were invoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

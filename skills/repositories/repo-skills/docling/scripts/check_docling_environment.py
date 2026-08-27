#!/usr/bin/env python3
"""Read-only Docling environment preflight.

Checks imports, package metadata, CLI entry points, optional modules, and common
external binaries without converting documents, downloading models, or contacting
remote services.

Examples:
  python scripts/check_docling_environment.py
  python scripts/check_docling_environment.py --as-json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
from dataclasses import asdict, dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def check_distribution(name: str) -> Check:
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        return Check(f"dist:{name}", False, "not installed")
    return Check(f"dist:{name}", True, version)


def check_import(name: str) -> Check:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return Check(f"import:{name}", False, f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", "imported")
    return Check(f"import:{name}", True, str(version))


def check_binary(name: str) -> Check:
    path = shutil.which(name)
    return Check(f"binary:{name}", bool(path), path or "not on PATH")


def check_entry_point(command: str) -> Check:
    path = shutil.which(command)
    return Check(f"entry-point:{command}", bool(path), path or "not on PATH")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Docling environment without side effects")
    parser.add_argument("--as-json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    checks = [
        check_distribution("docling"),
        check_distribution("docling-slim"),
        check_distribution("docling-core"),
        check_import("docling"),
        check_import("docling.document_converter"),
        check_import("docling.document_extractor"),
        check_import("docling.chunking"),
        check_import("docling.service_client"),
        check_import("torch"),
        check_import("torchvision"),
        check_import("rapidocr"),
        check_import("tesserocr"),
        check_import("easyocr"),
        check_entry_point("docling"),
        check_entry_point("docling-tools"),
        check_binary("tesseract"),
        check_binary("ffmpeg"),
    ]

    payload = {"ok": all(check.ok for check in checks[:8]), "checks": [asdict(check) for check in checks]}
    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            status = "OK" if check.ok else "MISS"
            print(f"{status:4} {check.name}: {check.detail}")
        if not payload["ok"]:
            print("\nCore Docling checks failed; install full `docling` or the needed `docling-slim[...]` extras.")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

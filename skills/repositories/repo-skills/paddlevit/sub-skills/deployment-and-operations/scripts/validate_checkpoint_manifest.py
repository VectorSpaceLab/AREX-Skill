#!/usr/bin/env python3
"""Validate PaddleViT checkpoint/export paths without deserializing them.

Use ``--checkpoint`` for a dynamic ``.pdparams`` file, ``--export-prefix``
for the three files produced by ``paddle.jit.save``, or ``--quant-dir`` for the
PaddleSlim-style ``__model__``/``__params__`` pair. The probe is read-only: it
never loads pickle-like checkpoint contents, writes manifests, downloads files,
or removes/renames artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


STATIC_SUFFIXES = (".pdmodel", ".pdiparams", ".pdiparams.info")


def _describe(path: Path) -> Dict[str, Any]:
    """Return file metadata needed for a presence manifest."""
    exists = path.is_file()
    size = path.stat().st_size if exists else None
    return {"path": str(path), "exists": exists, "nonempty": bool(size), "size": size}


def _validate_files(kind: str, paths: Iterable[Path]) -> Dict[str, Any]:
    """Validate that all expected artifacts are regular, non-empty files."""
    files = [_describe(path) for path in paths]
    return {"kind": kind, "ok": all(item["exists"] and item["nonempty"] for item in files), "files": files}


def main() -> int:
    """Validate the requested artifact manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--checkpoint",
        action="append",
        type=Path,
        help="dynamic checkpoint file; repeat for multiple candidate files",
    )
    group.add_argument(
        "--export-prefix",
        type=Path,
        help="static export prefix, without .pdmodel/.pdiparams suffix",
    )
    group.add_argument(
        "--quant-dir",
        type=Path,
        help="PaddleSlim-style directory containing __model__ and __params__",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    records: List[Dict[str, Any]] = []
    if args.checkpoint:
        records.append(_validate_files("dynamic-checkpoint", args.checkpoint))
    elif args.export_prefix:
        if args.export_prefix.name.endswith(STATIC_SUFFIXES):
            records.append(
                {
                    "kind": "static-export",
                    "ok": False,
                    "error": "pass a prefix, not a path ending in a static artifact suffix",
                }
            )
        else:
            records.append(
                _validate_files(
                    "static-export",
                    [Path(str(args.export_prefix) + suffix) for suffix in STATIC_SUFFIXES],
                )
            )
    else:
        records.append(
            _validate_files(
                "paddleslim-quantized",
                [args.quant_dir / "__model__", args.quant_dir / "__params__"],
            )
        )

    report: Dict[str, Any] = {
        "ok": all(record["ok"] for record in records),
        "records": records,
        "interpretation": "presence/non-empty check only; parameter/model compatibility is unverified",
        "side_effects": "none: no network, deserialization, writes, renames, or deletion",
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PaddleViT checkpoint manifest (read-only)")
        for record in records:
            print(record)
        print(report["interpretation"])
        print(report["side_effects"])
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

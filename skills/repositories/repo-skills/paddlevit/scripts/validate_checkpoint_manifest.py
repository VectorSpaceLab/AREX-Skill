#!/usr/bin/env python3
"""Validate a PaddleViT checkpoint artifact prefix without loading tensors.

The helper checks path existence and common sibling files only. It does not
open, modify, delete, or download checkpoint contents.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect_prefix(prefix: str, kind: str) -> dict[str, object]:
    path = Path(prefix).expanduser()
    candidates = {
        "paddle": [path, Path(str(path) + ".pdparams"), Path(str(path) + ".pdopt")],
        "exported": [Path(str(path) + ".pdmodel"), Path(str(path) + ".pdiparams"), Path(str(path) + ".pdiparams.info")],
        "dino": [Path(str(path) + ".pdparams"), Path(str(path) + ".pdopt"), Path(str(path) + "_dino_loss.pdparams")],
    }[kind]
    rows = [{"path": str(item), "exists": item.exists(), "file": item.is_file()} for item in candidates]
    return {"prefix": str(path), "kind": kind, "artifacts": rows, "complete": all(row["exists"] and row["file"] for row in rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prefix", help="Checkpoint or exported-model prefix")
    parser.add_argument("--kind", choices=("paddle", "exported", "dino"), default="paddle")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    result = inspect_prefix(args.prefix, args.kind)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"kind={result['kind']} prefix={result['prefix']}")
        for row in result["artifacts"]:
            print(f"{'present' if row['exists'] else 'missing'}: {row['path']}")
        print(f"complete={result['complete']}")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

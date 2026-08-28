#!/usr/bin/env python3
"""Validate a merged FastVideo video/caption manifest without reading video bytes."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--manifest", default="videos2caption.json")
    args = parser.parse_args()
    root = Path(args.dataset_dir).resolve()
    manifest = root / args.manifest
    try:
        records = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid manifest: {exc}")
        return 2
    if not isinstance(records, list) or not records:
        print("invalid manifest: expected a non-empty JSON list")
        return 2
    seen = set()
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"[{index}] expected object")
            continue
        rel = record.get("path")
        cap = record.get("cap")
        if not isinstance(rel, str) or not rel.strip():
            errors.append(f"[{index}].path must be a non-empty string")
            continue
        if rel in seen:
            errors.append(f"[{index}].path duplicated: {rel}")
        seen.add(rel)
        if not isinstance(cap, str) or not cap.strip():
            errors.append(f"[{index}].cap must be a non-empty string")
        path = (root / "videos" / rel).resolve()
        if root not in path.parents and path != root:
            errors.append(f"[{index}].path escapes dataset: {rel}")
        elif not path.is_file():
            errors.append(f"[{index}] missing video: {path.relative_to(root)}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"valid records={len(records)} root={root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

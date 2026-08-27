#!/usr/bin/env python3
"""Read-only smoke check for a DataChain dc-knowledge/ tree.

This helper never imports DataChain, never reads `.datachain/db`, and never
creates, deletes, or modifies files. It validates the markdown knowledge-base
surface that agents read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_TREE = """dc-knowledge/
├── index.md
├── datasets/
│   ├── <local_dataset>.md
│   └── <namespace>/<project>/<studio_dataset>.md
├── buckets/
│   └── <scheme>/<bucket_or_bucket_prefix>.md
└── jobs/
    └── index.md        # optional Studio jobs analytics
"""

DATASET_FRONTMATTER = {
    "name",
    "last_version",
    "updated",
    "records",
    "known_versions",
}
BUCKET_FRONTMATTER = {"uri", "bucket", "scanned", "files", "size"}
INDEX_FRONTMATTER = {"generated"}


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text
    lines = stripped.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text
    fm: dict[str, str] = {}
    for raw in lines[1:end_idx]:
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    body = "\n".join(lines[end_idx + 1 :])
    return fm, body


def read_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(errors="replace")
    return split_frontmatter(text)[0]


def resolve_kb_path(path: Path, *, project_root: bool) -> Path:
    if project_root:
        return path / "dc-knowledge"
    if path.name == "dc-knowledge":
        return path
    nested = path / "dc-knowledge"
    if nested.exists():
        return nested
    return path


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def check_markdown_frontmatter(
    paths: list[Path], required: set[str], base: Path, warnings: list[str]
) -> None:
    for md in paths:
        fm = read_frontmatter(md)
        if not fm:
            warnings.append(f"{rel(md, base)} has no frontmatter")
            continue
        missing = sorted(required - set(fm))
        if missing:
            warnings.append(
                f"{rel(md, base)} frontmatter missing expected keys: "
                + ", ".join(missing)
            )


def validate(kb_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(kb_path),
        "exists": kb_path.exists(),
        "errors": [],
        "warnings": [],
        "info": {},
    }
    errors: list[str] = result["errors"]
    warnings: list[str] = result["warnings"]
    info: dict[str, Any] = result["info"]

    if not kb_path.exists():
        errors.append("knowledge base path does not exist")
        return result
    if not kb_path.is_dir():
        errors.append("knowledge base path is not a directory")
        return result

    index = kb_path / "index.md"
    datasets_dir = kb_path / "datasets"
    buckets_dir = kb_path / "buckets"
    jobs_index = kb_path / "jobs" / "index.md"

    if not index.exists():
        errors.append("missing index.md")
    else:
        check_markdown_frontmatter([index], INDEX_FRONTMATTER, kb_path, warnings)

    if not datasets_dir.exists():
        warnings.append("datasets/ directory is absent; no dataset pages found")
        dataset_mds: list[Path] = []
    else:
        dataset_mds = sorted(datasets_dir.rglob("*.md"))
        check_markdown_frontmatter(
            dataset_mds, DATASET_FRONTMATTER, kb_path, warnings
        )

    if not buckets_dir.exists():
        warnings.append("buckets/ directory is absent; no bucket pages found")
        bucket_mds: list[Path] = []
    else:
        bucket_mds = sorted(buckets_dir.rglob("*.md"))
        check_markdown_frontmatter(bucket_mds, BUCKET_FRONTMATTER, kb_path, warnings)

    json_intermediates = sorted(
        p
        for root in (datasets_dir, buckets_dir)
        if root.exists()
        for p in root.rglob("*.json")
    )
    if json_intermediates:
        warnings.append(
            "JSON intermediates remain under datasets/ or buckets/: "
            + ", ".join(rel(p, kb_path) for p in json_intermediates[:10])
            + (" ..." if len(json_intermediates) > 10 else "")
        )

    plan = kb_path / ".plan.json"
    info.update(
        {
            "index": index.exists(),
            "dataset_pages": len(dataset_mds),
            "bucket_pages": len(bucket_mds),
            "jobs_index": jobs_index.exists(),
            "plan_json": plan.exists(),
            "json_intermediates": len(json_intermediates),
        }
    )
    if index.exists() and not dataset_mds and not bucket_mds and not jobs_index.exists():
        warnings.append("index.md exists but no dataset, bucket, or jobs pages were found")
    return result


def print_human(result: dict[str, Any]) -> None:
    print(f"Knowledge base: {result['path']}")
    print(f"Exists: {result['exists']}")
    info = result.get("info") or {}
    if info:
        print(f"index.md: {'yes' if info.get('index') else 'no'}")
        print(f"dataset pages: {info.get('dataset_pages', 0)}")
        print(f"bucket pages: {info.get('bucket_pages', 0)}")
        print(f"jobs index: {'yes' if info.get('jobs_index') else 'no'}")
        print(f".plan.json: {'yes' if info.get('plan_json') else 'no'}")
        print(f"JSON intermediates: {info.get('json_intermediates', 0)}")
    for err in result.get("errors", []):
        print(f"ERROR: {err}")
    for warn in result.get("warnings", []):
        print(f"WARNING: {warn}")
    if not result.get("errors"):
        print("Smoke check completed without fatal errors.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or print the expected DataChain dc-knowledge/ markdown "
            "tree. This is read-only and never touches the Dataset DB."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="dc-knowledge",
        help=(
            "Path to dc-knowledge/ or to a project containing dc-knowledge/ "
            "(default: dc-knowledge)."
        ),
    )
    parser.add_argument(
        "--project-root",
        action="store_true",
        help="Treat PATH as a project root and inspect PATH/dc-knowledge.",
    )
    parser.add_argument(
        "--expected",
        action="store_true",
        help="Print the expected tree layout and exit successfully.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when warnings are present, not only errors.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.expected:
        print(EXPECTED_TREE.rstrip())
        return 0
    kb_path = resolve_kb_path(Path(args.path), project_root=args.project_root)
    result = validate(kb_path)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

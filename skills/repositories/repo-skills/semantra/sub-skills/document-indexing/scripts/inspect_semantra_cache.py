#!/usr/bin/env python3
"""Summarize Semantra cache artifacts without importing Semantra.

The script is read-only. Point it at the directory printed by
`semantra --show-semantra-dir` or the directory passed with `--semantra-dir`.

Examples:
  python inspect_semantra_cache.py --cache-dir ~/.config/semantra
  python inspect_semantra_cache.py --cache-dir ./semantra-cache --json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

KNOWN_SUFFIXES = {
    ".tokens.json": "tokens_json",
    ".config.json": "config_json",
    ".embeddings": "embeddings_binary",
    ".annoy": "annoy_index",
    ".pdf.txt": "converted_pdf_text",
    ".pdf.positions.json": "pdf_positions_json",
}

EMBEDDING_RE = re.compile(
    r"^(?P<md5>[0-9a-f]{1,64})\.(?P<config>[0-9a-f]{1,64})\.(?P<size>\d+)_(?P<offset>\d+)_(?P<rewind>\d+)\.embeddings$"
)
ANNOY_RE = re.compile(
    r"^(?P<md5>[0-9a-f]{1,64})\.(?P<config>[0-9a-f]{1,64})\.(?P<size>\d+)_(?P<offset>\d+)_(?P<rewind>\d+)\.(?P<trees>\d+)t\.annoy$"
)
CONFIG_RE = re.compile(r"^(?P<md5>[0-9a-f]{1,64})\.(?P<config>[0-9a-f]{1,64})\.config\.json$")
TOKENS_RE = re.compile(r"^(?P<md5>[0-9a-f]{1,64})\.(?P<config>[0-9a-f]{1,64})\.tokens\.json$")


def classify(path: Path) -> str:
    name = path.name
    # Check longer suffixes first.
    for suffix, kind in sorted(KNOWN_SUFFIXES.items(), key=lambda item: -len(item[0])):
        if name.endswith(suffix):
            return kind
    return "unknown"


def safe_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"error": repr(exc)}


def summarize(cache_dir: Path) -> dict[str, Any]:
    files = [p for p in cache_dir.iterdir() if p.is_file()]
    counts = Counter(classify(p) for p in files)
    by_config: dict[str, dict[str, Any]] = defaultdict(lambda: {"files": [], "windows": []})
    unknown = []

    for path in files:
        stat = path.stat()
        item = {"name": path.name, "bytes": stat.st_size, "kind": classify(path)}
        match = CONFIG_RE.match(path.name) or TOKENS_RE.match(path.name) or EMBEDDING_RE.match(path.name) or ANNOY_RE.match(path.name)
        if match:
            key = f"{match.group('md5')}.{match.group('config')}"
            item.update(match.groupdict())
            if match.re is EMBEDDING_RE or match.re is ANNOY_RE:
                by_config[key]["windows"].append(
                    {
                        "size": int(match.group("size")),
                        "offset": int(match.group("offset")),
                        "rewind": int(match.group("rewind")),
                        "kind": item["kind"],
                        "bytes": stat.st_size,
                        "trees": int(match.group("trees")) if "trees" in match.groupdict() and match.group("trees") else None,
                    }
                )
            if item["kind"] == "config_json":
                config = safe_json(path)
                item["config_summary"] = {
                    "base_filename": config.get("base_filename") if isinstance(config, dict) else None,
                    "num_dimensions": config.get("num_dimensions") if isinstance(config, dict) else None,
                    "windows": config.get("windows") if isinstance(config, dict) else None,
                    "num_embeddings": config.get("num_embeddings") if isinstance(config, dict) else None,
                    "use_annoy": config.get("use_annoy") if isinstance(config, dict) else None,
                    "semantra_version": config.get("semantra_version") if isinstance(config, dict) else None,
                }
            by_config[key]["files"].append(item)
        elif item["kind"] == "unknown":
            unknown.append(item)

    return {
        "cache_dir_exists": cache_dir.exists(),
        "file_count": len(files),
        "counts_by_kind": dict(counts),
        "documents_by_config_hash": dict(by_config),
        "unknown_files": unknown,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Files: {report['file_count']}")
    print("Kinds:")
    for kind, count in sorted(report["counts_by_kind"].items()):
        print(f"  - {kind}: {count}")
    print("\nDocument/config groups:")
    for key, group in sorted(report["documents_by_config_hash"].items()):
        print(f"  - {key}: {len(group['files'])} files")
        configs = [f for f in group["files"] if f["kind"] == "config_json"]
        for cfg in configs:
            summary = cfg.get("config_summary", {})
            print(
                "    config: "
                f"base={summary.get('base_filename')} dims={summary.get('num_dimensions')} "
                f"windows={summary.get('windows')} embeddings={summary.get('num_embeddings')} "
                f"annoy={summary.get('use_annoy')} version={summary.get('semantra_version')}"
            )
    if report["unknown_files"]:
        print("\nUnknown files:")
        for item in report["unknown_files"]:
            print(f"  - {item['name']} ({item['bytes']} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", required=True, help="Semantra cache directory to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir).expanduser().resolve()
    if not cache_dir.exists() or not cache_dir.is_dir():
        print(f"Cache directory does not exist or is not a directory: {cache_dir}")
        return 2
    report = summarize(cache_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

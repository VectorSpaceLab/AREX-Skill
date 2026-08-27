#!/usr/bin/env python3
"""Plan safe GPT Academic code-analysis file selection for a source tree."""
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path

DEFAULT_EXCLUDES = [".git", "node_modules", "__pycache__", ".pytest_cache", "dist", "build", ".venv", "venv"]
LANG_HINTS = {
    ".py": "解析整个Python项目",
    ".java": "解析整个Java项目",
    ".cpp": "解析整个C++项目（.cpp/.hpp/.c/.h）",
    ".c": "解析整个C++项目（.cpp/.hpp/.c/.h）",
    ".h": "解析整个C++项目（.cpp/.hpp/.c/.h）",
    ".hpp": "解析整个C++项目（.cpp/.hpp/.c/.h）",
    ".go": "解析整个Go项目",
    ".rs": "解析整个Rust项目",
    ".lua": "解析整个Lua项目",
    ".cs": "解析整个CSharp项目",
    ".m": "解析整个Matlab项目",
    ".ipynb": "解析Jupyter Notebook文件",
    ".md": "翻译README或MD / Markdown翻译",
}


def should_skip(path: Path, excludes):
    parts = set(path.parts)
    if parts.intersection(DEFAULT_EXCLUDES):
        return True
    return any(fnmatch.fnmatch(str(path), pat) or fnmatch.fnmatch(path.name, pat) for pat in excludes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="source tree or file visible to the GPT Academic server")
    parser.add_argument("--include", default="*", help="comma-separated fnmatch patterns")
    parser.add_argument("--exclude", default="", help="comma-separated exclusion patterns")
    parser.add_argument("--max-files", type=int, default=512, help="warning threshold")
    args = parser.parse_args()
    target = Path(args.path).expanduser().resolve()
    includes = [p.strip() for p in args.include.split(",") if p.strip()]
    excludes = [p.strip() for p in args.exclude.split(",") if p.strip()]
    if not target.exists():
        raise SystemExit(f"path does not exist: {target}")
    candidates = [target] if target.is_file() else [p for p in target.rglob("*") if p.is_file()]
    selected = []
    counts = {}
    skipped = 0
    for path in candidates:
        rel = path.relative_to(target) if target.is_dir() else path.name
        if should_skip(path, excludes):
            skipped += 1
            continue
        if not any(fnmatch.fnmatch(str(rel), pat) or fnmatch.fnmatch(path.name, pat) for pat in includes):
            skipped += 1
            continue
        suffix = path.suffix.lower() or "<none>"
        counts[suffix] = counts.get(suffix, 0) + 1
        selected.append(str(rel))
    suggested = sorted({LANG_HINTS.get(s) for s in counts if LANG_HINTS.get(s)})
    payload = {"target": str(target), "selected_count": len(selected), "skipped_count": skipped, "suffix_counts": counts, "suggested_plugins": suggested or ["解析项目源代码（手动指定和筛选源代码文件类型）"], "warnings": []}
    if len(selected) > args.max_files:
        payload["warnings"].append(f"selected_count exceeds {args.max_files}; split modules or add exclusions")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

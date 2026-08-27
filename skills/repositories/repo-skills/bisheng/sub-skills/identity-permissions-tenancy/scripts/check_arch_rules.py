#!/usr/bin/env python3
"""Read-only pattern scan for BiSheng permission, tenant, frontend, and loguru risks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = {
    "direct_roleaccess_or_role_access": re.compile(r"role[_]?access|RoleAccessDao|RoleAccess", re.I),
    "raw_tenant_id_sql": re.compile(r"tenant_id\s*=|WHERE\s+.*tenant_id", re.I),
    "frontend_direct_axios_import": re.compile(r"import\s+axios\s+from\s+['\"]axios['\"]"),
    "loguru_exc_info": re.compile(r"logger\.(debug|info|warning|error|exception)\([^\n]*exc_info\s*=", re.S),
    "bare_except_pass": re.compile(r"except\s+(Exception\s*)?:\s*\n\s*pass\b"),
}

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "__pycache__", "skills"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".sh"}:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for high-risk BiSheng architecture patterns.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    hits = []
    for path in iter_files(root):
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                hits.append((name, str(rel)))
                break
    print("BiSheng architecture-risk pattern scan")
    print("======================================")
    for name, rel in hits[: args.limit]:
        print(f"{name:32} {rel}")
    if len(hits) > args.limit:
        print(f"... {len(hits) - args.limit} more")
    print("\nNote: this is a conservative grep-style scanner. Review findings against docs/constitution.md and arch-guard output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

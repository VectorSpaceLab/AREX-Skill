#!/usr/bin/env python3
"""Check that Markdown links in the generated ML Glossary runtime are self-contained.

Local Markdown links must resolve inside the runtime directory. External URLs
are allowed as optional references. This script intentionally ignores generated
review/test artifacts because they live outside the runtime tree.

Example:
    python scripts/check_runtime_links.py .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

LINK_RE = re.compile(r"(?<!!)(?:\[[^\]]+\]\(([^)]+)\)|<([^>\s]+)>)")
ALLOWED_SCHEMES = {"http", "https", "mailto"}


def is_external(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in ALLOWED_SCHEMES


def strip_fragment(target: str) -> str:
    return target.split("#", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_root", nargs="?", default=".", help="Root of the generated runtime skill")
    args = parser.parse_args()

    root = Path(args.runtime_root).resolve()
    if not root.exists():
        print(f"ERROR: runtime root does not exist: {root}", file=sys.stderr)
        return 2

    failures: list[str] = []
    for md in sorted(root.rglob("*.md")):
        rel_md = md.relative_to(root)
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = (match.group(1) or match.group(2) or "").strip()
            if not target or target.startswith("#") or is_external(target):
                continue
            if target.startswith(("/", "~")):
                failures.append(f"{rel_md}: absolute/local-private link {target}")
                continue
            path_part = strip_fragment(target)
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                failures.append(f"{rel_md}: link escapes runtime: {target}")
                continue
            if not resolved.exists():
                failures.append(f"{rel_md}: missing local link target: {target}")

    if failures:
        print("Runtime link check FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Runtime link check passed for {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check generated LangChain skill Markdown links and common leakage patterns."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)]+)\)")
LEAK_PATTERNS = (
    "/root/",
    "/home/",
    "file://",
    "../scripts/",
    "../../examples",
    "../../docs",
    "conda activate",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", nargs="?", default=".", help="Generated skill directory")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    failures: list[str] = []

    for markdown in sorted(skill_dir.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for pattern in LEAK_PATTERNS:
            if pattern in text:
                failures.append(f"{markdown.relative_to(skill_dir)} contains leak pattern {pattern!r}")
        for target in LINK_RE.findall(text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            if target.startswith("/"):
                failures.append(f"{markdown.relative_to(skill_dir)} has absolute link {target}")
                continue
            link_path = (markdown.parent / target.split("#", 1)[0]).resolve()
            try:
                link_path.relative_to(skill_dir)
            except ValueError:
                failures.append(f"{markdown.relative_to(skill_dir)} links outside skill tree: {target}")
                continue
            if target.split("#", 1)[0] and not link_path.exists():
                failures.append(f"{markdown.relative_to(skill_dir)} missing link target: {target}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK skill links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

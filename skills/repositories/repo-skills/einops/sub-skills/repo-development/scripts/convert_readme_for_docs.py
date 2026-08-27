#!/usr/bin/env python3
"""Dry-run-first README-to-docs converter for einops-style docs.

The repository converter removes bare .mp4 URL lines from README.md and writes a
MkDocs index page. This bundled helper makes the input/output explicit and only
writes when --execute is supplied.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def convert_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("https://") and line.endswith(".mp4") and " " not in line:
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert einops README content into a MkDocs index file.")
    p.add_argument("--readme", default="README.md", help="README input path (default: README.md).")
    p.add_argument("--output", default="docs_src/index.md", help="Docs index output path (default: docs_src/index.md).")
    p.add_argument("--execute", action="store_true", help="Write the converted output. Default previews only.")
    p.add_argument("--preview-lines", type=int, default=20, help="Number of converted lines to preview in dry-run mode.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    readme = Path(args.readme)
    output = Path(args.output)
    if not readme.exists():
        raise SystemExit(f"README input not found: {readme}")
    converted = convert_text(readme.read_text(encoding="utf-8"))
    if args.execute:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(converted, encoding="utf-8")
        print(f"Wrote converted README to {output}")
    else:
        print(f"Dry-run: would write {len(converted.splitlines())} lines to {output}")
        print("--- preview ---")
        for line in converted.splitlines()[: args.preview_lines]:
            print(line)
        print("--- end preview ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

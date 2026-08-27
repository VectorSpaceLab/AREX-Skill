#!/usr/bin/env python3
"""Extract Python code blocks from Markdown for LaVague snippet review.

This is an adapted, safer variant of LaVague's docs-code extraction helper. It
writes outputs to an explicit destination directory and can optionally normalize
interactive snippets for smoke checking. It does not execute extracted code.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CODE_BLOCK_RE = re.compile(r"```(?:python|py)\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_python_code(markdown: str, normalize_live_calls: bool) -> str:
    blocks = CODE_BLOCK_RE.findall(markdown)
    code = "\n\n".join(block.strip() for block in blocks if block.strip())
    if normalize_live_calls:
        code = code.replace("agent.demo", "agent.run")
        code = re.sub(r",\s*display=True", "", code)
        code = re.sub(r"\bheadless=False\s*,\s*", "", code)
        code = re.sub(r"\bheadless=False\b", "", code)
        code = re.sub(r"\boptions=chrome_options\b", "", code)
        code = re.sub(r"display\(Image\(url\)\)", "", code)
    return code.rstrip() + ("\n" if code else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract LaVague-related Python code blocks from Markdown without executing them.")
    parser.add_argument("markdown", nargs="+", help="Markdown file(s) to inspect.")
    parser.add_argument("--output-dir", default="extracted_lavague_code", help="Destination directory for extracted .py files.")
    parser.add_argument("--normalize-live-calls", action="store_true", help="Replace some interactive/headed snippet calls with safer forms for smoke review.")
    parser.add_argument("--fail-empty", action="store_true", help="Exit non-zero if any input has no Python code blocks.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    generated = []
    for raw in args.markdown:
        src = Path(raw)
        text = src.read_text(encoding="utf-8")
        code = extract_python_code(text, args.normalize_live_calls)
        if not code.strip():
            print(f"{src}: no Python code blocks")
            if args.fail_empty:
                failures += 1
            continue
        target = out_dir / f"{src.stem}_extracted.py"
        target.write_text(code, encoding="utf-8")
        generated.append(target)
        print(f"{src}: wrote {target}")
    if generated:
        index = out_dir / "index.txt"
        index.write_text("\n".join(str(path) for path in generated) + "\n", encoding="utf-8")
        print(f"index: wrote {index}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract LaTeX math snippets from a local text/TeX file.

This helper uses pix2tex.dataset extraction logic when pix2tex is installed and
never performs network access.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract math snippets from a local TeX/text file")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", "-o", type=Path, default=None)
    parser.add_argument("--wiki", action="store_true", help="look for wiki-style displaymath snippets")
    parser.add_argument("--unescape", action="store_true", help="HTML-unescape input before extraction")
    parser.add_argument("--demacro", action="store_true", help="expand simple TeX newcommand/def macros before extraction")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    if args.unescape:
        text = html.unescape(text)
    if args.demacro:
        from pix2tex.dataset.demacro import pydemacro

        text = pydemacro(text)
    from pix2tex.dataset.extract_latex import find_math

    snippets = sorted(find_math(text, wiki=args.wiki))
    output = "\n".join(snippets)
    if output:
        output += "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if snippets else 2


if __name__ == "__main__":
    raise SystemExit(main())

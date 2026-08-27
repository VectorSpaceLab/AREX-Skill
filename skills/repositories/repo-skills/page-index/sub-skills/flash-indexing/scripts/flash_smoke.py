#!/usr/bin/env python3
"""No-LLM PageIndex Flash smoke check for a local PDF."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pageindex.flash import page_index_flash


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a no-LLM PageIndex Flash smoke check on one PDF")
    parser.add_argument("pdf", help="PDF path to inspect")
    parser.add_argument("--embedded-toc", action=argparse.BooleanOptionalAction, default=False,
                        help="Use embedded bookmarks when trustworthy (default: disabled for deterministic smoke)")
    parser.add_argument("--optimize", action=argparse.BooleanOptionalAction, default=True,
                        help="Run deterministic merge-only optimization (default: enabled)")
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.is_file():
        raise SystemExit(f"PDF not found: {pdf}")

    result = page_index_flash(
        str(pdf),
        summary=False,
        optimize=args.optimize,
        optimize_expand=False,
        use_embedded_toc=args.embedded_toc,
    )
    structure = result.get("structure") or []
    payload = {
        "status": "ok",
        "doc_name": result.get("doc_name"),
        "doc_title": result.get("doc_title"),
        "top_nodes": len(structure),
        "first_titles": [node.get("title") for node in structure[:5]],
        "optimize": result.get("optimize"),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline Markdown-to-tree smoke check for PageIndex."""
from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from pageindex import md_to_tree

SAMPLE = """# Smoke Document

## Section A
Text under A.

```python
# Not a heading inside code
```

**   **

## Section B
More text.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a no-LLM Markdown PageIndex smoke check")
    parser.add_argument("--md", help="Optional Markdown file path; a synthetic fixture is used when omitted")
    args = parser.parse_args()

    if args.md:
        md_path = Path(args.md)
    else:
        tmp = Path(tempfile.gettempdir()) / "pageindex_markdown_smoke.md"
        tmp.write_text(SAMPLE, encoding="utf-8")
        md_path = tmp

    result = asyncio.run(md_to_tree(
        md_path=str(md_path),
        if_thinning=False,
        if_add_node_summary="no",
        if_add_doc_description="no",
        if_add_node_text="no",
        if_add_node_id="yes",
    ))
    structure = result.get("structure") or []
    payload = {
        "status": "ok",
        "doc_name": result.get("doc_name"),
        "line_count": result.get("line_count"),
        "top_titles": [node.get("title") for node in structure],
        "first_child_titles": [node.get("title") for node in (structure[0].get("nodes") or [])] if structure else [],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

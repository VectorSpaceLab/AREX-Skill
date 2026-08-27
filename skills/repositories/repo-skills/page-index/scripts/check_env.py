#!/usr/bin/env python3
"""Import/signature smoke for a PageIndex-capable Python environment."""
from __future__ import annotations

import inspect
import json
import sys


def main() -> int:
    try:
        import pageindex
        from pageindex import PageIndexClient, get_document, get_document_structure, get_page_content
        from pageindex import md_to_tree, optimize_tree, page_index
        from pageindex.flash import page_index_flash
        from pageindex.tree_optimize import optimize
    except Exception as exc:  # noqa: BLE001 - smoke script should report import failures cleanly
        print(json.dumps({
            "status": "failed",
            "phase": "import",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": "Make the source package or installed package importable as `pageindex`, then rerun this smoke script.",
        }, indent=2))
        return 1

    signatures = {
        "pageindex.page_index": str(inspect.signature(page_index)),
        "pageindex.md_to_tree": str(inspect.signature(md_to_tree)),
        "pageindex.flash.page_index_flash": str(inspect.signature(page_index_flash)),
        "pageindex.optimize_tree": str(inspect.signature(optimize_tree)),
        "pageindex.tree_optimize.optimize": str(inspect.signature(optimize)),
        "PageIndexClient": str(inspect.signature(PageIndexClient)),
        "PageIndexClient.index": str(inspect.signature(PageIndexClient.index)),
        "PageIndexClient.get_document": str(inspect.signature(PageIndexClient.get_document)),
        "PageIndexClient.get_document_structure": str(inspect.signature(PageIndexClient.get_document_structure)),
        "PageIndexClient.get_page_content": str(inspect.signature(PageIndexClient.get_page_content)),
        "retrieve.get_document": str(inspect.signature(get_document)),
        "retrieve.get_document_structure": str(inspect.signature(get_document_structure)),
        "retrieve.get_page_content": str(inspect.signature(get_page_content)),
    }

    print(json.dumps({
        "status": "ok",
        "python": sys.version.split()[0],
        "module_file": getattr(pageindex, "__file__", None),
        "signatures": signatures,
        "notes": [
            "Flash extraction imports from `pageindex.flash`, not from the top-level package.",
            "This repository may not expose distribution metadata; import success is the primary package smoke.",
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

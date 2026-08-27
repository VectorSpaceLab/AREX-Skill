#!/usr/bin/env python3
"""Offline PageIndexClient workspace retrieval smoke check.

Creates a tiny temporary workspace with cached pages, then exercises
get_document, get_document_structure, and get_page_content without model calls
or external files.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pageindex import PageIndexClient

DOC_ID = "sample-doc"


def write_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    meta = {
        DOC_ID: {
            "type": "pdf",
            "doc_name": "sample.pdf",
            "doc_description": "Synthetic cached workspace document for PageIndexClient smoke testing.",
            "path": "sample.pdf",
            "page_count": 2,
        }
    }
    doc = {
        "id": DOC_ID,
        "type": "pdf",
        "path": "sample.pdf",
        "doc_name": "sample.pdf",
        "doc_description": meta[DOC_ID]["doc_description"],
        "page_count": 2,
        "structure": [
            {
                "title": "Overview",
                "node_id": "0000",
                "start_index": 1,
                "end_index": 2,
                "summary": "Two-page synthetic document used for retrieval smoke testing.",
            }
        ],
        "pages": [
            {"page": 1, "content": "Page 1 explains the purpose of the smoke test."},
            {"page": 2, "content": "Page 2 confirms page range retrieval works."},
        ],
    }
    (workspace / "_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (workspace / f"{DOC_ID}.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pageindex-workspace-smoke-") as tmp:
        workspace = Path(tmp)
        write_workspace(workspace)
        client = PageIndexClient(workspace=str(workspace))
        payload = {
            "status": "ok",
            "loaded_ids": sorted(client.documents),
            "metadata": json.loads(client.get_document(DOC_ID)),
            "structure": json.loads(client.get_document_structure(DOC_ID)),
            "pages": json.loads(client.get_page_content(DOC_ID, "1-2")),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

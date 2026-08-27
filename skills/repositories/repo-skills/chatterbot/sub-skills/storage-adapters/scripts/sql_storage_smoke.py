#!/usr/bin/env python3
"""Run a safe SQLStorageAdapter CRUD/filter smoke test."""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChatterBot SQL storage with an in-memory SQLite database.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    from chatterbot.storage import SQLStorageAdapter
    from chatterbot.conversation import Statement

    adapter = SQLStorageAdapter(database_uri=None, raise_on_missing_search_text=False)
    try:
        adapter.create(text="Hello", tags=["greeting"])
        statement = Statement(text="Hi there!", in_response_to="Hello", tags=["greeting", "bot"])
        adapter.update(statement)
        by_tag = list(adapter.filter(tags=["greeting"], order_by=["text"]))
        by_response = list(adapter.filter(in_response_to="Hello"))
        result = {
            "ok": True,
            "count": adapter.count(),
            "tag_results": [s.text for s in by_tag],
            "response_results": [s.text for s in by_response],
        }
    except Exception as exc:
        result = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
    finally:
        try:
            adapter.drop()
            adapter.close()
        except Exception:
            pass

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

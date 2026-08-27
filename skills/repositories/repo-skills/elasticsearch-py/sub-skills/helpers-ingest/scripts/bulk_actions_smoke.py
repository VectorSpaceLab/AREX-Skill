#!/usr/bin/env python3
"""Offline validation of common Elasticsearch bulk action shapes.

This helper never creates a client or sends a request. It checks that the
installed public helper turns representative actions into the expected bulk
header/body pair.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from elasticsearch.helpers import expand_action


def validate(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for action in actions:
        header, body = expand_action(action)
        results.append({"header": header, "body": body})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print normalized JSON")
    args = parser.parse_args()
    actions = [
        {"_index": "books", "_id": "1", "title": "Python"},
        {"_op_type": "update", "_index": "books", "_id": "1", "doc": {"rank": 1}},
        {"_op_type": "delete", "_index": "books", "_id": "old"},
    ]
    results = validate(actions)
    assert results[0]["header"] == {"index": {"_index": "books", "_id": "1"}}
    assert results[0]["body"] == {"title": "Python"}
    assert results[1]["header"] == {"update": {"_index": "books", "_id": "1"}}
    assert results[2]["header"] == {"delete": {"_index": "books", "_id": "old"}}
    assert results[2]["body"] is None
    if args.json:
        print(json.dumps(results, sort_keys=True))
    else:
        print(f"validated {len(results)} offline bulk actions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

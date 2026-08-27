#!/usr/bin/env python3
"""Build and assert a small Elasticsearch DSL request without network access."""

from __future__ import annotations

import argparse
import json

from elasticsearch.dsl import Q, Search


def build_request() -> dict:
    query = Q("bool", must=[Q("match", title="python")], filter=[Q("term", status="published")])
    return (
        Search(index="books")
        .query(query)
        .source(["title", "status"])
        .sort({"published_at": "desc"})
        .to_dict()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the rendered body")
    args = parser.parse_args()
    body = build_request()
    assert body["query"]["bool"]["must"] == [{"match": {"title": "python"}}]
    assert body["query"]["bool"]["filter"] == [{"term": {"status": "published"}}]
    assert body["_source"] == ["title", "status"]
    if args.json:
        print(json.dumps(body, indent=2, sort_keys=True))
    else:
        print("offline DSL request assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

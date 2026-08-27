#!/usr/bin/env python3
"""Render a parameterized ES|QL query without contacting Elasticsearch."""

from __future__ import annotations

import argparse

from elasticsearch.esql import E, ESQL


def build_query():
    return (
        ESQL.from_("employees")
        .keep("first_name", "last_name")
        .where(E("first_name") == E("?"))
        .eval(name_length="LENGTH(first_name)")
        .limit(10)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", action="store_true", help="print the rendered query")
    args = parser.parse_args()
    rendered = build_query().render()
    assert rendered.startswith("FROM employees")
    assert "WHERE first_name == ?" in rendered
    assert "KEEP first_name, last_name" in rendered
    assert "LIMIT 10" in rendered
    if args.show:
        print(rendered)
    else:
        print("offline ES|QL builder assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

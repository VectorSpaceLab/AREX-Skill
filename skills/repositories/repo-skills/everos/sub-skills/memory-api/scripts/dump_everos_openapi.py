#!/usr/bin/env python3
"""Dump or summarize EverOS OpenAPI from the installed package without lifespan."""
from __future__ import annotations

import argparse
import json
import os
import sys


def build_schema() -> dict:
    os.environ.setdefault("ENV", "DEV")
    from everos.entrypoints.api.app import create_app

    return create_app(lifespan_providers=[]).openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write JSON schema to this file instead of stdout")
    parser.add_argument("--summary", action="store_true", help="Print concise path summary")
    args = parser.parse_args()
    schema = build_schema()
    if args.summary:
        print(f"title: {schema.get('info', {}).get('title')}")
        print(f"version: {schema.get('info', {}).get('version')}")
        for path, methods in sorted(schema.get("paths", {}).items()):
            print(f"{path}: {', '.join(sorted(methods))}")
        return 0
    rendered = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline planner for R2R graph workflows."""

from __future__ import annotations

import argparse
import json

def main() -> int:
    parser = argparse.ArgumentParser(description="Plan the order of R2R graph extraction and lifecycle steps without contacting a server.")
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--document-id", help="Optional document ID when planning document-driven extraction.")
    parser.add_argument(
        "--mode",
        choices=("document-extract", "collection-extract", "build", "pull", "reset", "inspect"),
        default="inspect",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = {
        "collection_id": args.collection_id,
        "document_id": args.document_id,
        "mode": args.mode,
        "steps": [],
    }

    if args.mode == "document-extract":
        plan["steps"] = ["ingest the document", "call documents.extract", "call graphs.build", "inspect entities/relationships/communities"]
    elif args.mode == "collection-extract":
        plan["steps"] = ["confirm collection membership", "call collections.extract", "call graphs.pull or graphs.build", "inspect graph output"]
    elif args.mode == "build":
        plan["steps"] = ["confirm source ingestion", "call graphs.build", "inspect graph output"]
    elif args.mode == "pull":
        plan["steps"] = ["confirm the collection graph exists", "call graphs.pull", "inspect retrieved graph state"]
    elif args.mode == "reset":
        plan["steps"] = ["back up anything important", "call graphs.reset", "rebuild if needed"]
    else:
        plan["steps"] = ["check source ingestion", "check graph settings", "check collection membership", "choose extraction or build"]

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"Collection: {args.collection_id}")
        if args.document_id:
            print(f"Document: {args.document_id}")
        for step in plan["steps"]:
            print(f"- {step}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

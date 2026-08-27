#!/usr/bin/env python3
"""Run a safe CPU-only import and packaged-data smoke check for BDDL.

This helper never writes files, downloads corpora, invokes data generation, or
imports a simulator. It reports JSON to stdout and returns nonzero on a broken
package/data installation.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check BDDL importability and package-relative runtime data without side effects."
    )
    parser.add_argument(
        "--knowledge-base",
        choices=("none", "empty", "populated"),
        default="none",
        help="optionally construct an empty or generated-data-backed in-memory KnowledgeBase",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from bddl.activity import get_all_activities
        from bddl.object_taxonomy import ObjectTaxonomy

        result: dict[str, Any] = {
            "distribution": {"name": "bddl", "version": metadata.version("bddl")},
            "import": {"module": "bddl", "status": "ok"},
        }
        activities = get_all_activities()
        taxonomy = ObjectTaxonomy()
        result["packaged_data"] = {
            "activity_count": len(activities),
            "taxonomy_synset_count": len(taxonomy.get_all_synsets()),
        }

        if args.knowledge_base != "none":
            from bddl.knowledge_base import KnowledgeBase

            kb = KnowledgeBase(
                populate=args.knowledge_base == "populated",
                verbose=False,
                load_wordnet=False,
            )
            result["knowledge_base"] = {
                "mode": args.knowledge_base,
                "synsets": len(kb.all_synsets()),
                "categories": len(kb.all_categories()),
                "objects": len(kb.all_objects()),
                "tasks": len(kb.all_tasks()),
                "transition_rules": len(kb.all_transition_rules()),
            }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except metadata.PackageNotFoundError:
        print("bddl distribution metadata is missing; install bddl==3.7.0", file=sys.stderr)
        return 2
    except ModuleNotFoundError as exc:
        print(f"BDDL import failed because {exc.name or 'a dependency'} is missing", file=sys.stderr)
        return 2
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        print(
            "BDDL imported but packaged runtime data is missing or unreadable; "
            f"check the complete bddl==3.7.0 installation ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 3
    except Exception as exc:
        print(
            f"BDDL smoke check failed: {type(exc).__name__}; "
            "retry without --knowledge-base populated to isolate data population",
            file=sys.stderr,
        )
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

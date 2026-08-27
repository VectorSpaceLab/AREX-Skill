#!/usr/bin/env python3
"""Export a UMLS META release to a JSONL knowledge base.

This is a safe, local-data conversion helper used by the project workflows.
It reads the standard UMLS `META/` files and writes one JSON object per line.

Example:
    python scripts/export_umls_json.py --meta_path /path/to/UMLS/META --output_path /tmp/umls.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Optional

from scispacy import umls_utils


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta_path", required=True, help="Path to the UMLS META directory.")
    parser.add_argument("--output_path", required=True, help="Output JSONL file path.")
    parser.add_argument("--lang", default="ENG", help="Language subset to keep.")
    parser.add_argument("--source", default=None, help="Optional UMLS source identifier filter.")
    parser.add_argument(
        "--include-suppressed",
        action="store_true",
        help="Include suppressed concepts and definitions instead of filtering them out.",
    )
    return parser


def main(meta_path: str, output_path: str, lang: Optional[str], source: Optional[str], include_suppressed: bool) -> None:
    concept_details: Dict[str, Dict] = {}

    print("Reading concepts ...")
    umls_utils.read_umls_concepts(meta_path, concept_details, source, lang, not include_suppressed)
    print("Reading types ...")
    umls_utils.read_umls_types(meta_path, concept_details)
    print("Reading definitions ...")
    umls_utils.read_umls_definitions(meta_path, concept_details)

    for concept in concept_details.values():
        concept["aliases"] = list(set(concept["aliases"]))
        if "canonical_name" not in concept:
            aliases = concept["aliases"]
            concept["canonical_name"] = aliases[0]
            del aliases[0]
        concept.pop("is_from_preferred_source", None)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Exporting to {output} ...")
    with output.open("w", encoding="utf-8") as fout:
        for value in concept_details.values():
            fout.write(json.dumps(value) + "\n")
    print(f"DONE. Wrote {len(concept_details)} concepts.")


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(args.meta_path, args.output_path, args.lang, args.source, args.include_suppressed)

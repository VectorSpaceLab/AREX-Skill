#!/usr/bin/env python3
"""Render HTML from a caller-provided Unstructured elements JSON file."""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

def render_html_from_elements_json(input_path: Path, encoding: str = "utf-8") -> str:
    from unstructured.partition.html.transformations import unstructured_elements_to_ontology
    from unstructured.staging.base import elements_from_json

    elements = elements_from_json(filename=str(input_path), encoding=encoding)
    ontology_root = unstructured_elements_to_ontology(elements)
    return html.unescape(ontology_root.to_html())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render HTML from a JSON array of Unstructured elements. This adapts the repository "
            "rendered-HTML utility for caller-provided files and is most useful for element JSON "
            "compatible with HTML ontology rendering."
        ),
    )
    parser.add_argument("input", help="Path to a JSON array of Unstructured element dictionaries.")
    parser.add_argument("--output", "-o", help="Output HTML file. Defaults to stdout.")
    parser.add_argument("--encoding", default="utf-8", help="Input and output encoding. Default: utf-8.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    input_path = Path(args.input)

    try:
        rendered = render_html_from_elements_json(input_path, encoding=args.encoding)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding=args.encoding)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

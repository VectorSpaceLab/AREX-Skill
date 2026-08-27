#!/usr/bin/env python3
"""Validate supplied local GeoNode metadata syntax and explicit fields.

This helper is deliberately offline. It parses JSON or XML, optionally checks
caller-supplied top-level JSON keys or XML local element names, and never
contacts a CSW/OGC service or applies a schema transformation.
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUPPORTED_XML_ROOTS = {"MD_Metadata", "metadata", "Record", "GetRecordByIdResponse"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_local_names_with_content(root: ET.Element) -> set[str]:
    return {
        local_name(element.tag)
        for element in root.iter()
        if "".join(element.itertext()).strip()
    }


def parse_json(path: Path, required: list[str]) -> list[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("JSON metadata must be an object at the top level")
    missing = [field for field in required if field not in value or value[field] in (None, "")]
    if missing:
        raise ValueError("missing required JSON field(s): " + ", ".join(missing))
    return [f"JSON object with {len(value)} top-level field(s)"]


def parse_xml(path: Path, required: list[str]) -> list[str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read XML: {exc}") from exc
    lowered = raw.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise ValueError("DTD/entity declarations are not accepted by this local checker")
    try:
        root = ET.fromstring(raw)
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise ValueError(f"invalid XML: {exc}") from exc
    root_name = local_name(root.tag)
    if root_name not in SUPPORTED_XML_ROOTS:
        allowed = ", ".join(sorted(SUPPORTED_XML_ROOTS - {"GetRecordByIdResponse"}))
        raise ValueError(f"unsupported metadata XML root '{root_name}'; expected one of: {allowed}")
    names = xml_local_names_with_content(root)
    missing = [field for field in required if field not in names]
    if missing:
        raise ValueError("missing or empty required XML element(s): " + ", ".join(missing))
    return [f"XML root {root_name}", f"XML local element names with content: {len(names)}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse one local JSON/XML metadata file and check explicit required fields."
    )
    parser.add_argument("path", type=Path, help="local JSON or XML file")
    parser.add_argument(
        "--required-field",
        action="append",
        default=[],
        metavar="NAME",
        help="repeat to require a non-empty top-level JSON key or XML local element name",
    )
    args = parser.parse_args(argv)
    if not args.path.is_file():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 2
    try:
        suffix = args.path.suffix.lower()
        if suffix == ".json":
            details = parse_json(args.path, args.required_field)
        elif suffix in {".xml", ".xsd"}:
            details = parse_xml(args.path, args.required_field)
        else:
            raise ValueError("file extension must be .json or .xml")
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.path.name}")
    for detail in details:
        print(f"- {detail}")
    if args.required_field:
        print("- required checks: " + ", ".join(args.required_field))
    else:
        print("- required checks: none supplied (syntax-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Static checks for RAGFlow web endpoint constants and API key usage.

This helper is read-only. It scans a RAGFlow checkout or copied web/src tree
for endpoint-key drift, duplicate endpoint keys, and suspicious API-prefix use.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}
DIRECT_API_LITERAL = re.compile(r"[\"'`]([^\"'`]*(?:/api/v1|/v1)[^\"'`]*)[\"'`]")
DIRECT_API_USAGE = re.compile(r"\bapi\.([A-Za-z_$][\w$]*)\b")
DESTRUCTURED_API_USAGE = re.compile(
    r"\b(?:const|let|var)\s*\{(?P<body>[^{}]*?)\}\s*=\s*api\b", re.DOTALL
)
ENDPOINT_API_IMPORT = re.compile(r"\bfrom\s+[\"'][^\"']*(?:^|/)utils/api[\"']")
TOP_LEVEL_KEY = re.compile(r"^\s{2}([A-Za-z_$][\w$]*):")


@dataclass
class Location:
    path: str
    line: int
    detail: str


@dataclass
class EndpointDefinition:
    key: str
    line: int
    text: str
    prefix: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only static scan for RAGFlow web API endpoint keys, "
            "prefix use, duplicate definitions, and missing references."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="RAGFlow checkout root. The scanner uses <root>/web/src.",
    )
    parser.add_argument(
        "--web-src",
        type=Path,
        help="Path to a copied or checkout web/src directory.",
    )
    parser.add_argument(
        "--api-file",
        type=Path,
        help="Path to the endpoint constants file. Defaults to <web-src>/utils/api.ts.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--show-unused",
        action="store_true",
        help="Include endpoint keys that are defined but not referenced outside api.ts.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when duplicates, missing references, or suspicious prefixes are found.",
    )
    return parser.parse_args(argv)


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.web_src:
        web_src = args.web_src
    elif args.root:
        web_src = args.root / "web" / "src"
    else:
        cwd = Path.cwd()
        web_src = cwd if cwd.name == "src" and cwd.parent.name == "web" else cwd / "web" / "src"

    api_file = args.api_file or web_src / "utils" / "api.ts"
    return web_src.resolve(), api_file.resolve()


def iter_source_files(web_src: Path) -> Iterable[Path]:
    ignored_parts = {"node_modules", "dist", "coverage", ".umi", ".umi-test", ".umi-production"}
    for path in sorted(web_src.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def classify_prefix(text: str) -> str:
    has_rest = "restAPIv1" in text or "/api/v1" in text
    has_web = "webAPI" in text or re.search(r"(?<!api)/v1", text) is not None
    if has_rest and has_web:
        return "mixed"
    if has_rest:
        return "restAPIv1"
    if has_web:
        return "webAPI"
    return "none"


def parse_endpoint_definitions(api_file: Path) -> tuple[list[EndpointDefinition], list[Location]]:
    text = read_text(api_file)
    lines = text.splitlines()
    keys: list[tuple[str, int, int]] = []
    in_default = False

    for line_index, line in enumerate(lines, start=1):
        if not in_default and re.search(r"\bexport\s+default\s*\{", line):
            in_default = True
            continue
        if not in_default:
            continue
        if line.startswith("};") or line.strip() == "};":
            break
        match = TOP_LEVEL_KEY.match(line)
        if match:
            keys.append((match.group(1), line_index, line_index - 1))

    definitions: list[EndpointDefinition] = []
    duplicate_locations: list[Location] = []
    counts = Counter(key for key, _, _ in keys)
    for key, line_number_value, zero_based_index in keys:
        next_indices = [idx for _, _, idx in keys if idx > zero_based_index]
        end_index = min(next_indices) if next_indices else len(lines)
        block = "\n".join(lines[zero_based_index:end_index])
        definitions.append(
            EndpointDefinition(
                key=key,
                line=line_number_value,
                text=block.strip(),
                prefix=classify_prefix(block),
            )
        )
        if counts[key] > 1:
            duplicate_locations.append(
                Location(str(api_file), line_number_value, f"duplicate endpoint key: {key}")
            )

    return definitions, duplicate_locations


def extract_api_references(path: Path, text: str) -> dict[str, list[Location]]:
    references: dict[str, list[Location]] = defaultdict(list)

    for match in DIRECT_API_USAGE.finditer(text):
        key = match.group(1)
        references[key].append(Location(str(path), line_number(text, match.start()), "api.<key> reference"))

    for match in DESTRUCTURED_API_USAGE.finditer(text):
        body = match.group("body")
        base_line = line_number(text, match.start("body"))
        for part in body.split(","):
            stripped = part.strip()
            if not stripped or stripped.startswith("//"):
                continue
            stripped = re.sub(r"/\*.*?\*/", "", stripped).strip()
            key_match = re.match(r"([A-Za-z_$][\w$]*)(?:\s*:|\s*$)", stripped)
            if key_match:
                key = key_match.group(1)
                line_offset = body[: body.find(part)].count("\n") if part in body else 0
                references[key].append(Location(str(path), base_line + line_offset, "destructured api key"))

    return references


def scan_prefix_literals(path: Path, text: str, api_file: Path) -> list[Location]:
    findings: list[Location] = []
    for match in DIRECT_API_LITERAL.finditer(text):
        literal = match.group(1)
        line = line_number(text, match.start())
        compact = literal.replace("\\/", "/")
        has_duplicate_prefix = any(
            bad in compact
            for bad in (
                "/api/v1/api/v1",
                "/api/v1/v1",
                "/v1/api/v1",
                "/v1/v1",
            )
        )
        has_both_prefixes = "/api/v1" in compact and re.search(r"(?<!api)/v1", compact) is not None
        outside_api_constants = path.resolve() != api_file.resolve()
        if has_duplicate_prefix or has_both_prefixes:
            findings.append(Location(str(path), line, f"suspicious mixed API prefix literal: {literal}"))
        elif outside_api_constants and (compact.startswith("/api/v1") or compact.startswith("/v1")):
            findings.append(Location(str(path), line, f"direct API path literal outside endpoint constants: {literal}"))
    return findings


def compact_locations(locations: list[Location], limit: int = 20) -> list[dict[str, object]]:
    return [asdict(item) for item in locations[:limit]]


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    web_src, api_file = resolve_paths(args)

    errors: list[str] = []
    if not web_src.is_dir():
        errors.append(f"web source directory not found: {web_src}")
    if not api_file.is_file():
        errors.append(f"endpoint constants file not found: {api_file}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    definitions, duplicate_locations = parse_endpoint_definitions(api_file)
    definitions_by_key: dict[str, EndpointDefinition] = {definition.key: definition for definition in definitions}
    defined_keys = set(definitions_by_key)

    references: dict[str, list[Location]] = defaultdict(list)
    prefix_findings: list[Location] = []
    scanned_files = 0

    for path in iter_source_files(web_src):
        scanned_files += 1
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        if path.resolve() != api_file.resolve() and ENDPOINT_API_IMPORT.search(text):
            for key, locations in extract_api_references(path, text).items():
                references[key].extend(locations)
        prefix_findings.extend(scan_prefix_literals(path, text, api_file))

    referenced_keys = set(references)
    missing_keys = sorted(referenced_keys - defined_keys)
    unused_keys = sorted(defined_keys - referenced_keys)
    prefix_counts = Counter(definition.prefix for definition in definitions)
    mixed_definitions = [
        Location(str(api_file), definition.line, f"endpoint key has mixed/noisy prefix markers: {definition.key}")
        for definition in definitions
        if definition.prefix == "mixed"
    ]

    report = {
        "ok": not duplicate_locations and not missing_keys and not prefix_findings and not mixed_definitions,
        "web_src": str(web_src),
        "api_file": str(api_file),
        "scanned_files": scanned_files,
        "endpoint_count": len(definitions),
        "prefix_counts": dict(sorted(prefix_counts.items())),
        "duplicate_keys": compact_locations(duplicate_locations, limit=100),
        "missing_referenced_keys": {
            key: compact_locations(references[key], limit=10) for key in missing_keys
        },
        "mixed_endpoint_prefixes": compact_locations(mixed_definitions, limit=100),
        "prefix_findings": compact_locations(prefix_findings, limit=100),
    }
    if args.show_unused:
        report["unused_keys"] = unused_keys

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("RAGFlow web API static scan")
        print(f"  web source: {web_src}")
        print(f"  api file:   {api_file}")
        print(f"  files:      {scanned_files}")
        print(f"  endpoints:  {len(definitions)}")
        print("  prefixes:   " + ", ".join(f"{key}={value}" for key, value in sorted(prefix_counts.items())))

        def print_locations(title: str, locations: list[Location]) -> None:
            print(f"\n{title}: {len(locations)}")
            for item in locations[:20]:
                print(f"  - {item.path}:{item.line}: {item.detail}")
            if len(locations) > 20:
                print(f"  ... {len(locations) - 20} more")

        print_locations("Duplicate endpoint keys", duplicate_locations)
        print(f"\nMissing referenced endpoint keys: {len(missing_keys)}")
        for key in missing_keys[:20]:
            first = references[key][0]
            print(f"  - {key}: first seen at {first.path}:{first.line}")
        if len(missing_keys) > 20:
            print(f"  ... {len(missing_keys) - 20} more")

        print_locations("Mixed endpoint prefix definitions", mixed_definitions)
        print_locations("Suspicious/direct API prefix literals", prefix_findings)

        if args.show_unused:
            print(f"\nDefined but not referenced outside api.ts: {len(unused_keys)}")
            for key in unused_keys[:40]:
                definition = definitions_by_key[key]
                print(f"  - {key}: {api_file}:{definition.line}")
            if len(unused_keys) > 40:
                print(f"  ... {len(unused_keys) - 40} more")

    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

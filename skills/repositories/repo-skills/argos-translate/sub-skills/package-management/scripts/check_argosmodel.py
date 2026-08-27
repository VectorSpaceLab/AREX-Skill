#!/usr/bin/env python3
"""Validate an Argos Translate .argosmodel archive without installing it.

Example:
    python sub-skills/package-management/scripts/check_argosmodel.py translate-en_es.argosmodel
    python sub-skills/package-management/scripts/check_argosmodel.py --strict translate-en_es.argosmodel

This helper is read-only. It does not extract the archive to the Argos package
directory, download anything, or require the original source repository.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

RECOMMENDED_METADATA_KEYS = [
    "package_version",
    "argos_version",
    "from_code",
    "from_name",
    "to_code",
    "to_name",
    "links",
    "type",
]


def top_level_or_direct_member(names: list[str], member: str) -> bool:
    """Return True if a zip contains member at root or under one top-level dir."""
    if member in names:
        return True
    suffix = "/" + member
    return any(name.endswith(suffix) for name in names)


def has_directory(names: list[str], directory: str) -> bool:
    directory = directory.rstrip("/") + "/"
    if directory in names:
        return True
    suffix = "/" + directory
    return any(name.startswith(directory) or suffix in name for name in names)


def read_metadata(zf: zipfile.ZipFile, names: list[str]) -> tuple[dict | None, str | None]:
    candidates = [name for name in names if name == "metadata.json" or name.endswith("/metadata.json")]
    if not candidates:
        return None, None
    metadata_name = sorted(candidates, key=lambda n: (n.count("/"), n))[0]
    with zf.open(metadata_name) as fh:
        data = json.loads(fh.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("metadata.json must contain a JSON object")
    return data, metadata_name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Argos Translate .argosmodel archive.")
    parser.add_argument("archive", type=Path, help="Path to a .argosmodel zip archive")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a translation archive lacks model/ or tokenizer files.",
    )
    args = parser.parse_args(argv)

    archive = args.archive
    problems: list[str] = []
    warnings: list[str] = []

    if not archive.exists():
        print(f"ERROR: file does not exist: {archive}", file=sys.stderr)
        return 1
    if not zipfile.is_zipfile(archive):
        print(f"ERROR: not a zip archive: {archive}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        try:
            metadata, metadata_name = read_metadata(zf, names)
        except Exception as exc:  # noqa: BLE001 - diagnostic helper should report parse failures.
            print(f"ERROR: metadata.json is not parseable: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

        if metadata is None:
            print("ERROR: metadata.json not found in archive", file=sys.stderr)
            return 1

        print(f"archive: {archive}")
        print(f"metadata: {metadata_name}")
        for key in RECOMMENDED_METADATA_KEYS:
            value = metadata.get(key, "<missing>")
            print(f"metadata.{key}: {value}")

        pkg_type = metadata.get("type", "translate")
        has_model = has_directory(names, "model")
        has_sentencepiece = top_level_or_direct_member(names, "sentencepiece.model")
        has_bpe = top_level_or_direct_member(names, "bpe.model")
        has_readme = top_level_or_direct_member(names, "README.md")
        has_minisbd = has_directory(names, "minisbd")
        has_stanza = has_directory(names, "stanza")
        has_spacy = has_directory(names, "spacy")

        print(f"contains model/: {has_model}")
        print(f"contains sentencepiece.model: {has_sentencepiece}")
        print(f"contains bpe.model: {has_bpe}")
        print(f"contains README.md: {has_readme}")
        print(f"contains minisbd/: {has_minisbd}")
        print(f"contains stanza/: {has_stanza}")
        print(f"contains spacy/: {has_spacy}")
        print(f"member count: {len(names)}")

        for key in ["from_code", "to_code"]:
            if pkg_type == "translate" and not metadata.get(key):
                warnings.append(f"metadata.{key} is missing for a translate package")
        if pkg_type == "translate" and not has_model:
            problems.append("model/ directory is missing")
        if pkg_type == "translate" and not (has_sentencepiece or has_bpe):
            problems.append("neither sentencepiece.model nor bpe.model is present")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if problems:
        for problem in problems:
            print(f"STRICT-CHECK: {problem}", file=sys.stderr)
        return 2 if args.strict else 0

    print("archive check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Preview a minimal W&B artifact manifest without uploading anything.

This helper intentionally avoids wandb.init(), run creation, network calls, and
artifact logging. It validates artifact names/types and local paths, then prints a
JSON preview that future agents can use before switching to real W&B SDK calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

NAME_MAXLEN = 128
ARTIFACT_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-.]+$")
RESERVED_TYPE_PREFIX = "wandb-"
RESERVED_TYPES = {"job"}


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def validate_artifact_name(name: str) -> str:
    if not name:
        fail("artifact name cannot be empty")
    if len(name) > NAME_MAXLEN:
        fail(f"artifact name must be at most {NAME_MAXLEN} characters")
    if not ARTIFACT_NAME_RE.fullmatch(name):
        fail("artifact name may only contain letters, numbers, underscores, hyphens, and dots")
    return name


def validate_artifact_type(artifact_type: str) -> str:
    if not artifact_type:
        fail("artifact type cannot be empty")
    if len(artifact_type) > NAME_MAXLEN:
        fail(f"artifact type must be at most {NAME_MAXLEN} characters")
    if "/" in artifact_type or ":" in artifact_type:
        fail("artifact type must not contain '/' or ':'")
    if artifact_type in RESERVED_TYPES or artifact_type.startswith(RESERVED_TYPE_PREFIX):
        fail("artifact type is reserved for W&B internal use")
    return artifact_type


def parse_mapping(value: str, default_logical: str | None = None) -> tuple[Path, str]:
    physical_text, sep, logical = value.partition(":")
    physical = Path(physical_text)
    logical_name = logical if sep else (default_logical or physical.name)
    validate_logical_path(logical_name)
    return physical, logical_name


def validate_logical_path(logical_path: str) -> str:
    if not logical_path or logical_path == ".":
        fail("artifact logical path cannot be empty or '.'")
    logical = Path(logical_path)
    if logical.is_absolute() or ".." in logical.parts:
        fail(f"artifact logical path must be relative and cannot traverse upward: {logical_path!r}")
    if os.sep != "/" and os.sep in logical_path:
        logical_path = logical_path.replace(os.sep, "/")
    return logical_path


def file_digest(path: Path) -> str:
    hasher = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def add_file_entry(entries: list[dict[str, Any]], physical: Path, logical_path: str) -> None:
    if not physical.is_file():
        fail(f"not a file: {physical}")
    entries.append(
        {
            "kind": "file",
            "logical_path": validate_logical_path(logical_path),
            "source": str(physical),
            "size": physical.stat().st_size,
            "md5": file_digest(physical),
        }
    )


def add_dir_entries(entries: list[dict[str, Any]], physical: Path, logical_root: str) -> None:
    if not physical.is_dir():
        fail(f"not a directory: {physical}")
    root = validate_logical_path(logical_root)
    for child in sorted(path for path in physical.rglob("*") if path.is_file()):
        relative = child.relative_to(physical).as_posix()
        logical_path = f"{root}/{relative}" if root else relative
        add_file_entry(entries, child, logical_path)


def add_reference_entry(entries: list[dict[str, Any]], reference: str) -> None:
    uri, sep, logical = reference.partition("=")
    if "://" not in uri:
        fail("references must include a URI scheme such as s3://, gs://, https://, or file://")
    logical_path = logical if sep and logical else uri.rstrip("/").split("/")[-1]
    entries.append(
        {
            "kind": "reference",
            "logical_path": validate_logical_path(logical_path),
            "uri": uri,
            "uploaded": False,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate artifact identity and preview local entries without uploading."
    )
    parser.add_argument("--name", required=True, help="Artifact name to validate.")
    parser.add_argument("--type", required=True, help="Artifact type to validate.")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="PATH[:LOGICAL_PATH]",
        help="Local file to include; logical path defaults to basename. Repeatable.",
    )
    parser.add_argument(
        "--dir",
        action="append",
        default=[],
        metavar="PATH[:LOGICAL_ROOT]",
        help="Local directory to include recursively; logical root defaults to basename. Repeatable.",
    )
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        metavar="URI[=LOGICAL_PATH]",
        help="External reference URI to preview without upload; use '=' to set a logical path. Repeatable.",
    )
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="Alias to preview. Repeatable; defaults to ['latest'] when omitted.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    name = validate_artifact_name(args.name)
    artifact_type = validate_artifact_type(args.type)

    entries: list[dict[str, Any]] = []
    for item in args.file:
        physical, logical = parse_mapping(item)
        add_file_entry(entries, physical, logical)
    for item in args.dir:
        physical, logical = parse_mapping(item)
        add_dir_entries(entries, physical, logical)
    for item in args.reference:
        add_reference_entry(entries, item)

    aliases = args.alias or ["latest"]
    for alias in aliases:
        if "/" in alias or ":" in alias:
            fail(f"alias must not contain '/' or ':': {alias!r}")

    preview = {
        "artifact": {"name": name, "type": artifact_type, "aliases": aliases},
        "entry_count": len(entries),
        "upload_planned": False,
        "entries": entries,
        "next_sdk_step": "Create wandb.Artifact, add the validated entries, then call run.log_artifact only when upload is intended.",
    }
    print(json.dumps(preview, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

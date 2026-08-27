#!/usr/bin/env python3
"""Validate a small Agents SDK sandbox manifest description without starting a sandbox."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

try:
    from agents.sandbox import Manifest, SandboxPathGrant
    from agents.sandbox.entries import BaseEntry
except Exception as exc:  # pragma: no cover - depends on caller environment
    print(
        json.dumps(
            {
                "ok": False,
                "errors": [f"failed to import sandbox APIs: {exc}"],
                "warnings": [],
                "summary": {},
            },
            indent=2,
        ),
        file=sys.stderr,
    )
    raise SystemExit(2) from exc

SENSITIVE_SEGMENTS = {
    ".aws",
    ".azure",
    ".config",
    ".docker",
    ".gnupg",
    ".kube",
    ".ssh",
}
BROAD_POSIX_GRANTS = {"/", "/home", "/Users", "/root", "/tmp", "/var", "/etc", "/opt"}
LOCAL_ENTRY_TYPES = {"local_file", "local_dir"}
MOUNT_ENTRY_TYPES = {
    "s3_mount",
    "gcs_mount",
    "r2_mount",
    "azure_blob_mount",
    "box_mount",
    "s3_files_mount",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a JSON manifest payload for Agents SDK sandbox APIs. The helper imports "
            "Manifest and entry classes, parses the payload, reports risky host path grants, "
            "and never starts a sandbox."
        )
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        help="Path to a JSON manifest payload. Omit or pass '-' to read stdin.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    parser.add_argument(
        "--allow-write-grants",
        action="store_true",
        help="Do not warn when extra_path_grants are writable.",
    )
    return parser.parse_args()


def load_payload(path: str | None) -> dict[str, Any]:
    if path in (None, "-"):
        raw = sys.stdin.read()
        source = "stdin"
    else:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        source = path

    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise TypeError(f"{source}: manifest payload must be a JSON object")
    return payload


def entry_type(entry: object) -> str | None:
    if isinstance(entry, BaseEntry):
        return entry.type
    if isinstance(entry, dict):
        value = entry.get("type")
        return value if isinstance(value, str) else None
    return None


def raw_entries(payload: dict[str, Any]) -> dict[str, Any]:
    entries = payload.get("entries", {})
    return entries if isinstance(entries, dict) else {}


def is_windows_absolute(value: str) -> bool:
    windows_path = PureWindowsPath(value)
    return windows_path.is_absolute() and not PurePosixPath(value.replace("\\", "/")).is_absolute()


def is_path_like(value: str) -> bool:
    return value.startswith(('/', '~')) or value.startswith(('.', '..')) or "/" in value or "\\" in value


def grant_warning(path: str, read_only: bool) -> list[str]:
    warnings: list[str] = []
    normalized = os.path.normpath(path)
    posix = path.replace("\\", "/")
    parts = set(PurePosixPath(posix).parts)
    if not read_only:
        warnings.append(f"grant {path!r} is writable; prefer read_only=True for source material")
    if normalized in BROAD_POSIX_GRANTS or posix in BROAD_POSIX_GRANTS:
        warnings.append(f"grant {path!r} is broad; prefer a concrete subdirectory")
    if parts & SENSITIVE_SEGMENTS:
        warnings.append(f"grant {path!r} includes a sensitive config/credential directory segment")
    return warnings


def local_source_warning(entry_path: str, entry: Any, grants: list[SandboxPathGrant]) -> list[str]:
    warnings: list[str] = []
    if not isinstance(entry, dict):
        return warnings
    src = entry.get("src")
    if not isinstance(src, str):
        return warnings
    if src.startswith("~"):
        warnings.append(f"entry {entry_path!r} uses a home-relative local source {src!r}")
    if is_windows_absolute(src):
        warnings.append(f"entry {entry_path!r} uses a Windows absolute local source {src!r}")
    elif PurePosixPath(src).is_absolute():
        covered = any(src == grant.path or src.startswith(grant.path.rstrip("/") + "/") for grant in grants)
        if not covered:
            warnings.append(
                f"entry {entry_path!r} uses absolute local source {src!r} without a matching grant"
            )
    if any(segment in SENSITIVE_SEGMENTS for segment in PurePosixPath(src.replace("\\", "/")).parts):
        warnings.append(f"entry {entry_path!r} local source {src!r} contains sensitive directory segment")
    return warnings


def raw_entry_warnings(payload: dict[str, Any], manifest: Manifest, allow_write_grants: bool) -> list[str]:
    warnings: list[str] = []
    entries = raw_entries(payload)
    grants = list(manifest.extra_path_grants)

    for key, value in entries.items():
        key_text = str(key)
        kind = entry_type(value)
        if key_text.startswith("/") or is_windows_absolute(key_text):
            warnings.append(f"entry key {key_text!r} is absolute; manifest parsing should reject it")
        if ".." in PurePosixPath(key_text.replace("\\", "/")).parts:
            warnings.append(f"entry key {key_text!r} contains '..'; manifest parsing should reject escapes")
        if kind in LOCAL_ENTRY_TYPES:
            warnings.extend(local_source_warning(key_text, value, grants))
        if kind in MOUNT_ENTRY_TYPES:
            read_only = value.get("read_only", True) if isinstance(value, dict) else True
            if not read_only:
                warnings.append(f"remote mount {key_text!r} is writable; confirm write-back is required")
            warnings.append(f"remote mount {key_text!r} is ephemeral and will not be copied into snapshots")

    if not allow_write_grants:
        for grant in grants:
            warnings.extend(grant_warning(grant.path, grant.read_only))

    return warnings


def validate(payload: dict[str, Any], allow_write_grants: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest: Manifest | None = None

    try:
        manifest = Manifest.model_validate(payload)
        list(manifest.iter_entries())
    except Exception as exc:
        errors.append(str(exc))

    summary: dict[str, Any] = {
        "entry_count": len(raw_entries(payload)),
        "registered_entry_types": sorted(BaseEntry.registered_types()),
    }

    if manifest is not None:
        try:
            summary.update(
                {
                    "root": manifest.root,
                    "validated_entry_paths": [path.as_posix() for path, _entry in manifest.iter_entries()],
                    "extra_path_grants": [
                        {"path": grant.path, "read_only": grant.read_only}
                        for grant in manifest.extra_path_grants
                    ],
                    "mount_targets": [path.as_posix() for _mount, path in manifest.mount_targets()],
                    "ephemeral_persistence_paths": sorted(
                        path.as_posix() for path in manifest.ephemeral_persistence_paths()
                    ),
                }
            )
        except Exception as exc:
            warnings.append(f"manifest parsed but summary failed: {exc}")
        warnings.extend(raw_entry_warnings(payload, manifest, allow_write_grants))
    else:
        for key, value in raw_entries(payload).items():
            if entry_type(value) in LOCAL_ENTRY_TYPES and isinstance(value, dict):
                src = value.get("src")
                if isinstance(src, str) and is_path_like(src):
                    warnings.append(f"entry {key!r} local source {src!r} could not be grant-checked")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}


def print_text(result: dict[str, Any]) -> None:
    status = "OK" if result["ok"] else "FAILED"
    print(f"Manifest validation: {status}")
    summary = result.get("summary", {})
    if summary:
        print("Summary:")
        for key in ("root", "entry_count", "validated_entry_paths", "extra_path_grants"):
            if key in summary:
                print(f"  {key}: {summary[key]}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args.manifest)
        result = validate(payload, allow_write_grants=args.allow_write_grants)
    except Exception as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": [], "summary": {}}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

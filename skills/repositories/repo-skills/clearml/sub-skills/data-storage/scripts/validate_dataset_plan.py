#!/usr/bin/env python3
"""Validate a JSON ClearML dataset plan using only the standard library.

The validator is intentionally offline: it does not import ClearML, read local
ClearML configuration, or contact any backend.
"""

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_ALLOWED_STORAGE_PREFIXES = ("s3://", "gs://", "azure://", "file://", "/", "./", "../")
_CREDENTIAL_PATTERN = re.compile(r"(?i)(access_key|secret|token|password)=")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+:-]*$")
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _pathish(value: str) -> bool:
    return bool(value.strip()) and "\x00" not in value


def validate_plan(plan: Mapping[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(plan, Mapping):
        return ["plan root must be a JSON object"], warnings

    project = plan.get("project")
    name = plan.get("name")
    version = plan.get("version")
    dataset_id = plan.get("dataset_id")
    storage = plan.get("storage")
    parents = _as_list(plan.get("parents"))
    add_files = _as_list(plan.get("add_files"))
    external_links = _as_list(plan.get("external_links"))
    sync_folders = _as_list(plan.get("sync_folders"))
    actions = _as_list(plan.get("actions"))

    if not _is_non_empty_string(dataset_id):
        if not _is_non_empty_string(name):
            errors.append("either dataset_id or name is required")
        if project is not None and not _is_non_empty_string(project):
            errors.append("project must be a non-empty string when provided")
    elif not _ID_PATTERN.match(dataset_id):
        errors.append("dataset_id contains unexpected characters")

    if version is not None:
        if not _is_non_empty_string(version):
            errors.append("version must be a non-empty string when provided")
        elif not _VERSION_PATTERN.match(version):
            errors.append("version contains whitespace or unsupported characters")

    if storage is not None:
        if not _is_non_empty_string(storage):
            errors.append("storage must be a non-empty string when provided")
        else:
            if _CREDENTIAL_PATTERN.search(storage):
                errors.append("storage URI appears to contain credentials")
            if not storage.startswith(_ALLOWED_STORAGE_PREFIXES):
                warnings.append("storage URI uses an uncommon scheme; verify ClearML storage support")
            if storage.startswith("s3://"):
                warnings.append("s3 storage requires configured credentials and the ClearML s3 extra")
            elif storage.startswith("gs://"):
                warnings.append("gs storage requires configured credentials and the ClearML gs extra")
            elif storage.startswith("azure://"):
                warnings.append("azure storage requires configured credentials and the ClearML azure extra")

    _validate_string_list(parents, "parents", errors, pattern=_ID_PATTERN)
    if dataset_id and parents:
        warnings.append("parents are ignored when mutating an existing dataset_id; create a new child dataset instead")

    for index, entry in enumerate(add_files):
        _validate_path_entry(entry, "add_files[{}]".format(index), errors, require_source_key="path")
    for index, entry in enumerate(external_links):
        _validate_path_entry(entry, "external_links[{}]".format(index), errors, require_source_key="uri")
    for index, entry in enumerate(sync_folders):
        _validate_path_entry(entry, "sync_folders[{}]".format(index), errors, require_source_key="folder")

    if add_files and sync_folders:
        warnings.append("plan mixes add_files and sync_folders; ensure removals from sync are intentional")
    if external_links and storage:
        warnings.append("external links are references; storage controls uploads for local files, not linked-object credentials")

    _validate_actions(actions, errors, warnings)

    if "close" in actions and "upload" not in actions and (add_files or sync_folders):
        if plan.get("close_auto_upload") is False:
            errors.append("close without upload is invalid when close_auto_upload is false and local changes exist")
        else:
            warnings.append("close may auto-upload pending changes; add upload first for explicit control")

    if plan.get("close_disable_upload") and "upload" not in actions and (add_files or sync_folders):
        errors.append("close_disable_upload requires an upload action before close when local changes exist")

    if plan.get("no_uploads") and ({"upload", "close"} & set(actions)):
        errors.append("no_uploads conflicts with upload or close actions")

    return errors, warnings


def _validate_string_list(values: Sequence[Any], field: str, errors: List[str], pattern: Optional[re.Pattern] = None) -> None:
    seen = set()
    for index, value in enumerate(values):
        label = "{}[{}]".format(field, index)
        if not _is_non_empty_string(value):
            errors.append("{} must be a non-empty string".format(label))
            continue
        if pattern and not pattern.match(value):
            errors.append("{} contains unexpected characters".format(label))
        if value in seen:
            errors.append("{} duplicates an earlier value".format(label))
        seen.add(value)


def _validate_path_entry(entry: Any, label: str, errors: List[str], require_source_key: str) -> None:
    if isinstance(entry, str):
        source = entry
        dataset_folder = None
    elif isinstance(entry, Mapping):
        source = entry.get(require_source_key)
        dataset_folder = entry.get("dataset_folder")
    else:
        errors.append("{} must be a string or object".format(label))
        return

    if not _is_non_empty_string(source) or not _pathish(source):
        errors.append("{}.{!s} must be a non-empty path/URI".format(label, require_source_key))
    if dataset_folder is not None:
        if not _is_non_empty_string(dataset_folder):
            errors.append("{}.dataset_folder must be a non-empty string when provided".format(label))
        elif dataset_folder.startswith("/") or ".." in dataset_folder.split("/"):
            errors.append("{}.dataset_folder must be a relative dataset path".format(label))


def _validate_actions(actions: Sequence[Any], errors: List[str], warnings: List[str]) -> None:
    allowed = {"create", "add", "sync", "upload", "close", "get", "verify", "list", "compare"}
    if not actions:
        warnings.append("actions is empty; plan validates structure only")
        return

    normalized: List[str] = []
    for index, action in enumerate(actions):
        if not _is_non_empty_string(action):
            errors.append("actions[{}] must be a non-empty string".format(index))
            continue
        action = action.strip()
        normalized.append(action)
        if action not in allowed:
            errors.append("actions[{}] is not one of {}".format(index, ", ".join(sorted(allowed))))

    positions = {action: index for index, action in enumerate(normalized)}
    if "upload" in positions and "close" in positions and positions["upload"] > positions["close"]:
        errors.append("upload must come before close")
    if "create" in positions:
        for action in ("add", "sync", "upload", "close"):
            if action in positions and positions[action] < positions["create"]:
                errors.append("{} cannot come before create".format(action))
    if "sync" in positions and "add" in positions:
        warnings.append("actions include both sync and add; verify intended semantics")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate an offline ClearML dataset plan JSON file.")
    parser.add_argument("plan", help="Path to JSON plan, or '-' for stdin")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Return failure when warnings are present")
    parser.add_argument("--quiet", action="store_true", help="Only print errors and warnings")
    args = parser.parse_args(argv)

    try:
        plan = _load_json(args.plan)
    except Exception as exc:
        print("error: failed to read plan: {}".format(exc), file=sys.stderr)
        return 2

    errors, warnings = validate_plan(plan)
    for warning in warnings:
        print("warning: {}".format(warning), file=sys.stderr)
    for error in errors:
        print("error: {}".format(error), file=sys.stderr)

    if errors or (warnings and args.warnings_as_errors):
        return 1
    if not args.quiet:
        print("dataset plan is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Build and validate a shell-safe clearml-task command without running it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

TASK_TYPES = {
    "training",
    "testing",
    "inference",
    "data_processing",
    "application",
    "monitor",
    "optimizer",
    "service",
    "qc",
    "custom",
}

LIST_FIELDS = {"tags", "args", "packages"}
BOOL_FIELDS = {
    "skip_task_init",
    "force_no_requirements",
    "skip_repo_detection",
    "skip_python_env_install",
    "pipeline",
    "pipeline_dont_add_run_number",
}
STRING_FIELDS = {
    "project",
    "name",
    "repo",
    "branch",
    "commit",
    "folder",
    "script",
    "binary",
    "module",
    "cwd",
    "queue",
    "requirements",
    "docker",
    "docker_args",
    "docker_bash_setup_script",
    "output_uri",
    "task_type",
    "base_task_id",
    "import_offline_session",
    "pipeline_version",
}
FIELD_TO_FLAG = {
    "output_uri": "--output-uri",
    "task_type": "--task-type",
    "skip_task_init": "--skip-task-init",
    "base_task_id": "--base-task-id",
    "import_offline_session": "--import-offline-session",
    "force_no_requirements": "--force-no-requirements",
    "skip_repo_detection": "--skip-repo-detection",
    "skip_python_env_install": "--skip-python-env-install",
    "pipeline_version": "--pipeline-version",
    "pipeline_dont_add_run_number": "--pipeline-dont-add-run-number",
}
FIELD_ORDER = [
    "project",
    "name",
    "tags",
    "repo",
    "branch",
    "commit",
    "folder",
    "script",
    "binary",
    "module",
    "cwd",
    "args",
    "queue",
    "requirements",
    "packages",
    "docker",
    "docker_args",
    "docker_bash_setup_script",
    "output_uri",
    "task_type",
    "skip_task_init",
    "base_task_id",
    "import_offline_session",
    "force_no_requirements",
    "skip_repo_detection",
    "skip_python_env_install",
    "pipeline",
    "pipeline_version",
    "pipeline_dont_add_run_number",
]


class CommandError(ValueError):
    """Validation error for command construction."""


def _as_list(value: Any, field: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    raise CommandError(f"{field} must be a string or a list of strings")


def _load_json(path: Optional[str], inline_json: Optional[str]) -> Dict[str, Any]:
    if path and inline_json:
        raise CommandError("provide either --json-file or --json, not both")
    if path:
        try:
            with Path(path).expanduser().open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError as exc:
            raise CommandError(f"could not read JSON file: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"invalid JSON file: {exc}") from exc
    elif inline_json:
        try:
            data = json.loads(inline_json)
        except json.JSONDecodeError as exc:
            raise CommandError(f"invalid JSON: {exc}") from exc
    else:
        data = {}
    if not isinstance(data, MutableMapping):
        raise CommandError("JSON input must be an object")
    return dict(data)


def _merge_cli(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    merged = dict(config)
    for field in sorted(STRING_FIELDS):
        value = getattr(args, field, None)
        if value is not None:
            merged[field] = value
    for field in sorted(LIST_FIELDS):
        value = getattr(args, field, None)
        if value is not None:
            merged[field] = value
    for field in sorted(BOOL_FIELDS):
        value = getattr(args, field, False)
        if value:
            merged[field] = True
    return merged


def _normalize(config: Mapping[str, Any]) -> Dict[str, Any]:
    known = STRING_FIELDS | LIST_FIELDS | BOOL_FIELDS
    unknown = sorted(set(config) - known)
    if unknown:
        raise CommandError("unknown field(s): " + ", ".join(unknown))

    normalized: Dict[str, Any] = {}
    for field in STRING_FIELDS:
        value = config.get(field)
        if value is not None:
            if not isinstance(value, (str, int, float)):
                raise CommandError(f"{field} must be a string")
            normalized[field] = str(value)
    for field in LIST_FIELDS:
        values = _as_list(config.get(field), field)
        if values:
            normalized[field] = values
    for field in BOOL_FIELDS:
        value = config.get(field, False)
        if isinstance(value, str):
            value = value.lower() in {"1", "true", "yes", "on"}
        normalized[field] = bool(value)
    return normalized


def _validate_key_values(values: Sequence[str], field: str) -> None:
    for item in values:
        if "=" not in item or item.startswith("="):
            raise CommandError(f"{field} entries must use key=value format: {item!r}")


def validate_config(config: Mapping[str, Any], *, allow_draft: bool = False) -> None:
    importing_offline = bool(config.get("import_offline_session"))
    base_task = bool(config.get("base_task_id"))

    if importing_offline:
        incompatible = [
            field
            for field in ("repo", "folder", "script", "module", "base_task_id", "requirements", "packages", "docker")
            if config.get(field)
        ]
        if incompatible:
            raise CommandError("--import-offline-session cannot be combined with " + ", ".join(incompatible))
        return

    if not config.get("name"):
        raise CommandError("--name is required unless --import-offline-session is used")
    if not config.get("project") and not base_task:
        raise CommandError("--project is required unless --base-task-id is used")

    if config.get("script") and config.get("module"):
        raise CommandError("--script and --module are mutually exclusive")

    entry_count = sum(bool(config.get(field)) for field in ("script", "module", "base_task_id"))
    if entry_count == 0:
        raise CommandError("choose an entrypoint: --script, --module, or --base-task-id")

    if config.get("repo") and config.get("folder"):
        raise CommandError("use either --repo or --folder, not both")

    if not base_task and not config.get("repo") and not config.get("folder") and not config.get("skip_repo_detection"):
        raise CommandError("provide --repo/--folder or explicitly use --skip-repo-detection")

    if config.get("task_type") and config["task_type"] not in TASK_TYPES:
        raise CommandError("invalid --task-type; expected one of " + ", ".join(sorted(TASK_TYPES)))

    if config.get("force_no_requirements"):
        conflicts = [field for field in ("requirements", "packages") if config.get(field)]
        if conflicts:
            raise CommandError("--force-no-requirements conflicts with " + ", ".join(conflicts))

    if config.get("pipeline_version") and not config.get("pipeline"):
        raise CommandError("--pipeline-version requires --pipeline")
    if config.get("pipeline_dont_add_run_number") and not config.get("pipeline"):
        raise CommandError("--pipeline-dont-add-run-number requires --pipeline")

    if config.get("args"):
        _validate_key_values(config["args"], "--args")

    if not config.get("queue") and not allow_draft:
        raise CommandError("--queue is missing; pass --allow-draft to build a draft-only task command")


def build_command(config: Mapping[str, Any]) -> List[str]:
    command = ["clearml-task"]
    for field in FIELD_ORDER:
        value = config.get(field)
        if field in BOOL_FIELDS:
            if value:
                command.append(FIELD_TO_FLAG.get(field, "--" + field.replace("_", "-")))
        elif field in LIST_FIELDS:
            values = value or []
            if values:
                command.append("--" + field.replace("_", "-"))
                command.extend(values)
        elif value not in (None, ""):
            command.append(FIELD_TO_FLAG.get(field, "--" + field.replace("_", "-")))
            command.append(str(value))
    return command


def shell_join(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a validated shell-safe clearml-task command without executing it."
    )
    parser.add_argument("--json-file", help="Path to a JSON object containing command fields")
    parser.add_argument("--json", help="Inline JSON object containing command fields")
    parser.add_argument("--allow-draft", action="store_true", help="Allow commands without --queue")

    for field in sorted(STRING_FIELDS):
        parser.add_argument("--" + field.replace("_", "-"), dest=field)
    parser.add_argument("--tags", nargs="*")
    parser.add_argument("--args", nargs="*")
    parser.add_argument("--packages", nargs="*")
    for field in sorted(BOOL_FIELDS):
        parser.add_argument("--" + field.replace("_", "-"), dest=field, action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        loaded = _load_json(args.json_file, args.json)
        merged = _merge_cli(loaded, args)
        normalized = _normalize(merged)
        validate_config(normalized, allow_draft=args.allow_draft)
        print(shell_join(build_command(normalized)))
    except CommandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

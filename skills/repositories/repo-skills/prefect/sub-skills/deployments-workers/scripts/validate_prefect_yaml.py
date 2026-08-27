#!/usr/bin/env python3
"""Validate a Prefect deployment YAML file without contacting a Prefect API.

The validator is intentionally self-contained. It uses PyYAML and jsonschema when
available, but falls back to JSON parsing plus focused structural checks. It does
not import Prefect, start services, access the network, or mutate files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOP_LEVEL_KEYS = {"prefect-version", "name", "build", "push", "pull", "deployments"}
DEPLOYMENT_KEYS = {
    "name",
    "version",
    "version_type",
    "tags",
    "description",
    "schedule",
    "schedules",
    "paused",
    "concurrency_limit",
    "flow_name",
    "entrypoint",
    "parameters",
    "enforce_parameter_schema",
    "build",
    "push",
    "pull",
    "work_pool",
    "triggers",
    "sla",
}
WORK_POOL_KEYS = {"name", "work_queue_name", "job_variables"}
SCHEDULE_KEYS = {
    "cron",
    "interval",
    "rrule",
    "timezone",
    "anchor_date",
    "active",
    "parameters",
    "slug",
    "replaces",
    "day_or",
}
SCHEDULE_SELECTORS = ("cron", "interval", "rrule")
FILE_ENTRYPOINT_PATTERN = re.compile(r"^[^:]+\.py:[A-Za-z_][\w.]*$")
MODULE_ENTRYPOINT_PATTERN = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_][\w.]*$")


class SimpleYamlError(ValueError):
    def __init__(self, line_number: int, message: str) -> None:
        super().__init__(f"line {line_number}: {message}")
        self.line_number = line_number
        self.message = message


def strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def split_unquoted_colon(text: str) -> tuple[str, str] | None:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == ":" and quote is None:
            if index == len(text) - 1 or text[index + 1].isspace():
                return text[:index], text[index + 1 :]
    return None


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        try:
            return json.loads(value) if value.startswith('"') else value[1:-1].replace("''", "'")
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> Any:
    """Parse a conservative YAML subset used by typical prefect.yaml files."""

    lines: list[tuple[int, str, int]] = []
    for line_number, original in enumerate(text.splitlines(), 1):
        if "\t" in original[: len(original) - len(original.lstrip())]:
            raise SimpleYamlError(line_number, "Tabs are not supported for indentation")
        without_comment = strip_yaml_comment(original).rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        lines.append((indent, without_comment.strip(), line_number))

    if not lines:
        return None

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return None, index
        current_indent, content, line_number = lines[index]
        if current_indent < indent:
            return None, index
        if current_indent > indent:
            indent = current_indent
        if content.startswith("- ") or content == "-":
            return parse_list(index, indent)
        return parse_mapping(index, indent)

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        items: list[Any] = []
        while index < len(lines):
            current_indent, content, line_number = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SimpleYamlError(line_number, "Unexpected indentation in list")
            if not (content.startswith("- ") or content == "-"):
                break

            item_text = content[1:].strip()
            index += 1
            if item_text == "":
                if index < len(lines) and lines[index][0] > indent:
                    item, index = parse_block(index, lines[index][0])
                else:
                    item = None
                items.append(item)
                continue

            key_value = split_unquoted_colon(item_text)
            if key_value is None:
                items.append(parse_scalar(item_text))
                continue

            key, raw_value = key_value
            key = key.strip().strip('"').strip("'")
            if not key:
                raise SimpleYamlError(line_number, "List item mapping has an empty key")
            mapping: dict[str, Any] = {}
            if raw_value.strip() == "":
                if index < len(lines) and lines[index][0] > indent:
                    value, index = parse_block(index, lines[index][0])
                else:
                    value = None
            else:
                value = parse_scalar(raw_value)
            mapping[key] = value

            while index < len(lines) and lines[index][0] > indent:
                extra, index = parse_block(index, lines[index][0])
                if isinstance(extra, dict):
                    mapping.update(extra)
                else:
                    raise SimpleYamlError(lines[index - 1][2], "List item continuation must be a mapping")
            items.append(mapping)
        return items, index

    def parse_mapping(index: int, indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        while index < len(lines):
            current_indent, content, line_number = lines[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SimpleYamlError(line_number, "Unexpected indentation in mapping")
            if content.startswith("- ") or content == "-":
                break
            key_value = split_unquoted_colon(content)
            if key_value is None:
                raise SimpleYamlError(line_number, "Expected 'key: value' mapping entry")
            key, raw_value = key_value
            key = key.strip().strip('"').strip("'")
            if not key:
                raise SimpleYamlError(line_number, "Mapping key cannot be empty")
            index += 1
            if raw_value.strip() == "":
                if index < len(lines) and lines[index][0] > indent:
                    value, index = parse_block(index, lines[index][0])
                else:
                    value = None
            else:
                value = parse_scalar(raw_value)
            mapping[key] = value
        return mapping, index

    parsed, next_index = parse_block(0, lines[0][0])
    if next_index != len(lines):
        raise SimpleYamlError(lines[next_index][2], "Could not parse the remaining document")
    return parsed


@dataclass
class Finding:
    level: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}


def _add(findings: list[Finding], level: str, path: str, message: str) -> None:
    findings.append(Finding(level=level, path=path, message=message))


def load_prefect_file(path: Path) -> tuple[Any | None, list[Finding], str]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _add(findings, "error", str(path), f"Could not read file: {exc}")
        return None, findings, "unreadable"

    if not text.strip():
        _add(findings, "error", str(path), "File is empty")
        return None, findings, "empty"

    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            return json.loads(text), findings, "json"
        except json.JSONDecodeError as exc:
            _add(findings, "error", str(path), f"Invalid JSON: {exc}")
            return None, findings, "json"

    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        try:
            return json.loads(text), findings, "json-fallback"
        except json.JSONDecodeError:
            try:
                loaded = parse_simple_yaml(text)
            except SimpleYamlError as exc:
                _add(
                    findings,
                    "error",
                    str(path),
                    f"PyYAML is not installed and the built-in YAML subset parser failed: {exc}",
                )
                return None, findings, "simple-yaml"
            _add(
                findings,
                "warning",
                str(path),
                "PyYAML is not installed; used a built-in YAML subset parser for structural checks.",
            )
            return loaded, findings, "simple-yaml"

    try:
        loaded = yaml.safe_load(text)
    except Exception as exc:
        _add(findings, "error", str(path), f"Invalid YAML: {exc}")
        return None, findings, "yaml"
    return loaded, findings, "yaml"


def load_schema(schema_path: Path | None, findings: list[Finding]) -> dict[str, Any] | None:
    if schema_path is None:
        return None
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:
        _add(findings, "error", str(schema_path), f"Could not read schema: {exc}")
    except json.JSONDecodeError as exc:
        _add(findings, "error", str(schema_path), f"Invalid schema JSON: {exc}")
    return None


def run_jsonschema(data: Any, schema: dict[str, Any] | None, findings: list[Finding]) -> None:
    if schema is None:
        return
    try:
        import jsonschema  # type: ignore[import-not-found]
    except Exception:
        _add(
            findings,
            "warning",
            "schema",
            "jsonschema is not installed; skipped full JSON Schema validation and ran built-in checks only.",
        )
        return

    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        path = format_path(error.path)
        _add(findings, "error", path, error.message)


def format_path(parts: Any) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def is_sequence(value: Any) -> bool:
    return isinstance(value, list)


def validate_actions(value: Any, path: str, findings: list[Finding]) -> None:
    if value is None:
        return
    if is_mapping(value):
        return
    if is_sequence(value):
        for index, step in enumerate(value):
            if not is_mapping(step):
                _add(findings, "error", f"{path}[{index}]", "Action steps must be mappings")
        return
    _add(findings, "error", path, "Action section must be null, a mapping, or a list of mappings")


def validate_schedule(schedule: Any, path: str, findings: list[Finding], strict_unknown: bool) -> None:
    if schedule in (None, {}):
        return
    if not is_mapping(schedule):
        _add(findings, "error", path, "Schedule must be a mapping")
        return

    if strict_unknown:
        for key in schedule:
            if key not in SCHEDULE_KEYS:
                _add(findings, "warning", f"{path}.{key}", "Unknown schedule field")

    selected = [key for key in SCHEDULE_SELECTORS if schedule.get(key) is not None]
    if len(selected) != 1:
        _add(
            findings,
            "error",
            path,
            "Schedule must set exactly one of 'cron', 'interval', or 'rrule'",
        )
    if "parameters" in schedule and not is_mapping(schedule.get("parameters")):
        _add(findings, "error", f"{path}.parameters", "Schedule parameters must be a mapping")
    timezone = schedule.get("timezone")
    if timezone is not None and not isinstance(timezone, str):
        _add(findings, "error", f"{path}.timezone", "Timezone must be a string")


def validate_schedules(value: Any, path: str, findings: list[Finding], strict_unknown: bool) -> None:
    if value is None:
        return
    if not is_sequence(value):
        _add(findings, "error", path, "Schedules must be a list")
        return
    replaces: dict[str, str] = {}
    for index, schedule in enumerate(value):
        schedule_path = f"{path}[{index}]"
        validate_schedule(schedule, schedule_path, findings, strict_unknown)
        if is_mapping(schedule) and schedule.get("replaces"):
            replaced = str(schedule["replaces"])
            if replaced in replaces:
                _add(
                    findings,
                    "error",
                    f"{schedule_path}.replaces",
                    f"Duplicate replaces target also used by {replaces[replaced]}",
                )
            else:
                replaces[replaced] = schedule_path


def validate_work_pool(value: Any, path: str, findings: list[Finding], strict_unknown: bool) -> None:
    if value is None:
        return
    if not is_mapping(value):
        _add(findings, "error", path, "work_pool must be a mapping")
        return
    if strict_unknown:
        for key in value:
            if key not in WORK_POOL_KEYS:
                _add(findings, "warning", f"{path}.{key}", "Unknown work_pool field")
    name = value.get("name")
    if name is not None and not isinstance(name, str):
        _add(findings, "error", f"{path}.name", "work_pool.name must be a string")
    queue = value.get("work_queue_name")
    if queue is not None and not isinstance(queue, str):
        _add(findings, "error", f"{path}.work_queue_name", "work_pool.work_queue_name must be a string")
    job_variables = value.get("job_variables")
    if job_variables is not None and not is_mapping(job_variables):
        _add(findings, "error", f"{path}.job_variables", "job_variables must be a mapping")


def validate_entrypoint(
    entrypoint: Any,
    path: str,
    manifest_dir: Path,
    findings: list[Finding],
    check_entrypoints: bool,
) -> None:
    if entrypoint in (None, ""):
        return
    if not isinstance(entrypoint, str):
        _add(findings, "error", path, "entrypoint must be a string")
        return
    if ":" not in entrypoint:
        _add(findings, "error", path, "entrypoint should include ':' as path.py:flow_function or module.path:flow_function")
        return

    target, function = entrypoint.split(":", 1)
    if not target or not function:
        _add(findings, "error", path, "entrypoint must include both target and flow function")
        return

    looks_like_file = target.endswith(".py") or os.sep in target or "/" in target
    if looks_like_file:
        if not FILE_ENTRYPOINT_PATTERN.match(entrypoint):
            _add(findings, "warning", path, "File entrypoints usually look like path/to/file.py:flow_function")
        if check_entrypoints:
            file_path = (manifest_dir / target).resolve()
            try:
                file_path.relative_to(manifest_dir.resolve())
            except ValueError:
                _add(findings, "warning", path, "Entrypoint file resolves outside the manifest directory")
            if not file_path.exists():
                _add(findings, "error", path, f"Entrypoint file does not exist: {target}")
            elif not file_path.is_file():
                _add(findings, "error", path, f"Entrypoint target is not a file: {target}")
    elif not MODULE_ENTRYPOINT_PATTERN.match(entrypoint):
        _add(findings, "warning", path, "Module entrypoints usually look like package.module:flow_function")


def validate_deployment(
    deployment: Any,
    path: str,
    manifest_dir: Path,
    findings: list[Finding],
    check_entrypoints: bool,
    strict_unknown: bool,
) -> None:
    if not is_mapping(deployment):
        _add(findings, "error", path, "Deployment entry must be a mapping")
        return

    if strict_unknown:
        for key in deployment:
            if key not in DEPLOYMENT_KEYS:
                _add(findings, "warning", f"{path}.{key}", "Unknown deployment field")

    name = deployment.get("name")
    if name is None:
        _add(findings, "warning", f"{path}.name", "Deployment has no name; CLI entrypoint deployment may require --name")
    elif not isinstance(name, str):
        _add(findings, "error", f"{path}.name", "Deployment name must be a string")

    validate_entrypoint(deployment.get("entrypoint"), f"{path}.entrypoint", manifest_dir, findings, check_entrypoints)

    if deployment.get("entrypoint") in (None, ""):
        _add(findings, "warning", f"{path}.entrypoint", "Deployment has no entrypoint; provide one in YAML or on the CLI")

    parameters = deployment.get("parameters")
    if parameters is not None and not is_mapping(parameters):
        _add(findings, "error", f"{path}.parameters", "parameters must be a mapping")

    tags = deployment.get("tags")
    if tags is not None and not isinstance(tags, (str, list)):
        _add(findings, "error", f"{path}.tags", "tags must be a string, list, or templated value")

    triggers = deployment.get("triggers")
    if triggers is not None:
        if not is_sequence(triggers):
            _add(findings, "error", f"{path}.triggers", "triggers must be a list of mappings")
        else:
            for index, trigger in enumerate(triggers):
                if not is_mapping(trigger):
                    _add(findings, "error", f"{path}.triggers[{index}]", "trigger must be a mapping")

    concurrency = deployment.get("concurrency_limit")
    if concurrency is not None and not isinstance(concurrency, (int, dict)):
        _add(findings, "error", f"{path}.concurrency_limit", "concurrency_limit must be an integer or mapping")

    if deployment.get("schedule") not in (None, {}) and deployment.get("schedules"):
        _add(findings, "error", path, "Use only one of 'schedule' or 'schedules' on a deployment")
    validate_schedule(deployment.get("schedule"), f"{path}.schedule", findings, strict_unknown)
    validate_schedules(deployment.get("schedules"), f"{path}.schedules", findings, strict_unknown)

    for action_name in ("build", "push", "pull"):
        validate_actions(deployment.get(action_name), f"{path}.{action_name}", findings)

    validate_work_pool(deployment.get("work_pool"), f"{path}.work_pool", findings, strict_unknown)


def validate_builtin(
    data: Any,
    manifest_dir: Path,
    findings: list[Finding],
    check_entrypoints: bool,
    strict_unknown: bool,
) -> None:
    if data is None:
        _add(findings, "error", "$", "Manifest is empty")
        return
    if not is_mapping(data):
        _add(findings, "error", "$", "Prefect YAML root must be a mapping")
        return

    if strict_unknown:
        for key in data:
            if key not in TOP_LEVEL_KEYS:
                _add(findings, "warning", f"$.{key}", "Unknown top-level field")

    for action_name in ("build", "push", "pull"):
        validate_actions(data.get(action_name), f"$.{action_name}", findings)

    deployments = data.get("deployments", [])
    if deployments is None:
        deployments = []
    if not is_sequence(deployments):
        _add(findings, "error", "$.deployments", "deployments must be a list")
        return
    if not deployments:
        _add(findings, "warning", "$.deployments", "No deployments are defined")
    for index, deployment in enumerate(deployments):
        validate_deployment(
            deployment,
            f"$.deployments[{index}]",
            manifest_dir,
            findings,
            check_entrypoints,
            strict_unknown,
        )


def summarize(findings: list[Finding]) -> dict[str, Any]:
    errors = sum(1 for finding in findings if finding.level == "error")
    warnings = sum(1 for finding in findings if finding.level == "warning")
    return {"ok": errors == 0, "errors": errors, "warnings": warnings}


def print_text(findings: list[Finding]) -> None:
    summary = summarize(findings)
    status = "OK" if summary["ok"] else "FAILED"
    print(f"{status}: {summary['errors']} error(s), {summary['warnings']} warning(s)")
    for finding in findings:
        print(f"{finding.level.upper()}: {finding.path}: {finding.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate a prefect.yaml-like deployment manifest without contacting Prefect services.",
    )
    parser.add_argument("--file", required=True, help="Path to prefect.yaml, YAML, or JSON manifest to validate.")
    parser.add_argument(
        "--check-entrypoints",
        action="store_true",
        help="Check that file-style entrypoint targets exist relative to the manifest directory.",
    )
    parser.add_argument(
        "--strict-unknown",
        action="store_true",
        help="Warn about unknown top-level, deployment, work_pool, and schedule keys.",
    )
    parser.add_argument(
        "--schema",
        help="Optional JSON Schema file to validate with when jsonschema is installed.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manifest_path = Path(args.file)
    data, findings, parser_name = load_prefect_file(manifest_path)
    schema = load_schema(Path(args.schema), findings) if args.schema else None

    if data is not None:
        run_jsonschema(data, schema, findings)
        validate_builtin(
            data,
            manifest_path.resolve().parent,
            findings,
            check_entrypoints=args.check_entrypoints,
            strict_unknown=args.strict_unknown,
        )

    summary = summarize(findings)
    if args.format == "json":
        print(
            json.dumps(
                {
                    **summary,
                    "file": str(manifest_path),
                    "parser": parser_name,
                    "findings": [finding.as_dict() for finding in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(findings)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

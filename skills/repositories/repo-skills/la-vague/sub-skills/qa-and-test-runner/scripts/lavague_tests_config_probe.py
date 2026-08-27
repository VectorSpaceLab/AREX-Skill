#!/usr/bin/env python3
"""Inspect a LaVague test-site config and print the matching lavague-test command.

This probe is YAML-only: it does not start a browser, a static server, or a
live LaVague agent.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import yaml
except Exception as exc:  # pragma: no cover - import guard
    yaml = None
    _YAML_IMPORT_ERROR = exc
else:
    _YAML_IMPORT_ERROR = None


OPERATORS = ["is not", "does not contain", "is lower than", "is greater than", "contains", "is"]
ALLOWED_PROPERTIES = {"URL", "Status", "Output", "Steps", "HTML", "Tabs"}
EXPECTATION_RE = re.compile(r"^\s*(.+?)\s+(is not|does not contain|is lower than|is greater than|contains|is)\s+(.+?)\s*$")


@dataclass
class Issue:
    level: str
    message: str


class ValidationError(Exception):
    pass


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ValidationError(f"PyYAML is not available: {_YAML_IMPORT_ERROR}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        raise ValidationError(f"Failed to parse YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError("Top-level YAML value must be a mapping")
    return data


def _resolve_config_path(path: Path) -> Tuple[Path, Path]:
    if path.is_dir():
        config = path / "config.yml"
        if not config.exists():
            raise ValidationError(f"Directory does not contain config.yml: {path}")
        return path, config
    if path.name != "config.yml":
        raise ValidationError("Pass either a config.yml file or a site directory")
    if not path.exists():
        raise ValidationError(f"Config file not found: {path}")
    return path.parent, path


def _parse_expectation(expr: Any) -> List[Issue]:
    issues: List[Issue] = []
    if not isinstance(expr, str):
        return [Issue("error", f"Expectation must be a string, got {type(expr).__name__}")]
    m = EXPECTATION_RE.match(expr)
    if not m:
        return [Issue("error", f"Invalid expectation syntax: {expr!r}")]
    prop, op, value = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    if prop not in ALLOWED_PROPERTIES:
        issues.append(Issue("error", f"Unknown property {prop!r}; use one of {sorted(ALLOWED_PROPERTIES)}"))
    if op not in OPERATORS:
        issues.append(Issue("error", f"Unknown operator {op!r}; use one of {OPERATORS}"))
    if not value:
        issues.append(Issue("error", f"Expectation {expr!r} is missing a value"))
    if prop == "Steps" and op in {"is lower than", "is greater than", "is", "is not"}:
        if not re.fullmatch(r"-?\d+", value):
            issues.append(Issue("warning", "Steps comparisons usually work best with integer values"))
    return issues


def _validate_task(task: Dict[str, Any], index: int, setup_type: str) -> List[Issue]:
    issues: List[Issue] = []

    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        issues.append(Issue("error", f"Task {index + 1} is missing a prompt"))

    url = task.get("url")
    if setup_type != "static" and (not isinstance(url, str) or not url.strip()):
        issues.append(Issue("error", f"Task {index + 1} is missing a url"))
    if setup_type == "static" and not isinstance(url, str):
        issues.append(Issue("warning", f"Task {index + 1} does not set url; static setups usually still pin it explicitly"))

    for field in ("max_steps", "n_attempts"):
        if field in task and not isinstance(task[field], int):
            issues.append(Issue("error", f"Task {index + 1} field {field} must be an integer"))

    user_data = task.get("user_data")
    if user_data is not None and not isinstance(user_data, dict):
        issues.append(Issue("error", f"Task {index + 1} user_data must be a mapping"))

    expect = task.get("expect")
    if expect is None:
        issues.append(Issue("warning", f"Task {index + 1} has no expect checks"))
    else:
        items = expect if isinstance(expect, list) else [expect]
        for item in items:
            issues.extend(_parse_expectation(item))

    return issues


def _format_command(args: argparse.Namespace, site_dir: Path, site_name: str) -> str:
    pieces = ["lavague-test", "--directory", str(site_dir.parent), "--site", site_name]
    if args.context:
        pieces.extend(["--context", args.context])
    if args.display:
        pieces.append("--display")
    if args.log_to_db:
        pieces.append("--log-to-db")
    return " ".join(shlex.quote(piece) for piece in pieces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a LaVague site config and print the matching lavague-test command."
    )
    parser.add_argument("--config", required=True, type=Path, help="Path to a config.yml file or a site directory")
    parser.add_argument("--directory", type=Path, help="Override the site root directory used in the printed command")
    parser.add_argument("--site", help="Override the site name used in the printed command")
    parser.add_argument("--context", help="Optional context Python file to include in the printed command")
    parser.add_argument("--display", action="store_true", help="Include --display in the printed command")
    parser.add_argument("--log-to-db", action="store_true", help="Include --log-to-db in the printed command")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    site_dir, config_path = _resolve_config_path(args.config.expanduser())
    if args.directory:
        site_root = args.directory.expanduser()
        site_dir = site_root / (args.site or site_dir.name)
    else:
        site_root = site_dir.parent
    site_name = args.site or site_dir.name

    if not config_path.exists():
        raise ValidationError(f"Config file not found: {config_path}")

    data = _load_yaml(config_path)
    issues: List[Issue] = []

    setup_type = data.get("type", "web")
    if "type" not in data:
        issues.append(Issue("warning", "Top-level `type` is omitted; add `type: web` for portability"))
    elif setup_type not in {"web", "static"}:
        issues.append(Issue("warning", f"Unknown top-level type {setup_type!r}; expected web or static"))

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValidationError("Top-level `tasks` must be a non-empty list")

    if not isinstance(data.get("user_data", {}), dict):
        raise ValidationError("Top-level `user_data` must be a mapping when present")
    for field in ("max_steps", "n_attempts"):
        if field in data and not isinstance(data[field], int):
            raise ValidationError(f"Top-level {field} must be an integer when present")

    if setup_type == "static":
        static_dir = data.get("directory", "www")
        if not isinstance(static_dir, str) or not static_dir.strip():
            issues.append(Issue("error", "Static configs need a directory string"))
        else:
            resolved_static_dir = (site_dir / static_dir).resolve()
            if not resolved_static_dir.exists():
                issues.append(Issue("warning", f"Static directory does not exist yet: {static_dir}"))
        port = data.get("port", 8000)
        if not isinstance(port, int):
            issues.append(Issue("error", "Static config port must be an integer"))

    total_expectations = 0
    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValidationError(f"Task {idx + 1} must be a mapping")
        task_issues = _validate_task(task, idx, setup_type)
        total_expectations += len(task.get("expect", [])) if isinstance(task.get("expect"), list) else int(task.get("expect") is not None)
        issues.extend(task_issues)

    errors = [issue.message for issue in issues if issue.level == "error"]
    warnings = [issue.message for issue in issues if issue.level == "warning"]
    if errors:
        for message in errors:
            print(f"Error: {message}", file=sys.stderr)
        raise ValidationError("Site config validation failed")

    print(f"Config: {config_path}")
    print(f"Site folder: {site_dir}")
    print(f"Setup type: {setup_type}")
    print(f"Tasks: {len(tasks)}")
    print(f"Expectations: {total_expectations}")
    if warnings:
        for message in warnings:
            print(f"Warning: {message}", file=sys.stderr)
    print(_format_command(args, site_dir, site_name))
    print("No browser or LaVague agent was launched by this probe.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

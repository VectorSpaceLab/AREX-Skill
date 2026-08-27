#!/usr/bin/env python3
"""Print a deterministic DVC pipeline plan without importing or executing DVC.

The input is JSON, or a small YAML-ish subset that can be parsed without third
party dependencies. The planner prints shell commands and validation checks only;
it never calls DVC, imports DVC, reads repository metadata, or executes stage
commands.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _parse_yamlish(text: str) -> dict[str, Any]:
    """Parse a tiny YAML-ish subset for simple pipeline plans.

    Supported shapes are top-level keys, lists of scalar values, and a `stages:`
    list whose items are mappings. This is intentionally small and deterministic;
    use JSON for nested or ambiguous plans.
    """

    result: dict[str, Any] = {}
    current_key: str | None = None
    current_stage: dict[str, Any] | None = None
    current_stage_key: str | None = None

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if not raw_line.startswith(" ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            current_stage = None
            current_stage_key = None
            result.setdefault(current_key, [])
            continue
        if not raw_line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            result[key.strip()] = _parse_scalar(value)
            current_key = key.strip()
            current_stage = None
            current_stage_key = None
            continue
        if current_key == "stages" and current_stage is not None and indent > 2:
            if stripped.startswith("- "):
                if current_stage_key is None:
                    raise ValueError(f"line {line_number}: list item has no parent key")
                current_stage.setdefault(current_stage_key, []).append(
                    _parse_scalar(stripped[2:])
                )
                continue
        if current_key == "stages" and stripped.startswith("- ") and indent <= 2:
            item = stripped[2:]
            current_stage = {}
            current_stage_key = None
            result.setdefault("stages", []).append(current_stage)
            if item:
                if ":" not in item:
                    raise ValueError(f"line {line_number}: stage item must be key: value")
                key, value = item.split(":", 1)
                current_stage[key.strip()] = _parse_scalar(value)
            continue
        if current_key == "stages" and current_stage is not None:
            if ":" not in stripped:
                raise ValueError(f"line {line_number}: expected key: value")
            key, value = stripped.split(":", 1)
            key = key.strip()
            if value.strip():
                current_stage[key] = _parse_scalar(value)
                current_stage_key = None
            else:
                current_stage[key] = []
                current_stage_key = key
            continue
        if current_key and stripped.startswith("- "):
            result.setdefault(current_key, []).append(_parse_scalar(stripped[2:]))
            continue
        raise ValueError(f"line {line_number}: unsupported YAML-ish syntax")

    return result


def load_spec(path: str | None, inline: str | None) -> dict[str, Any]:
    if path and inline:
        raise SystemExit("error: use either --spec or --inline, not both")
    if path:
        text = Path(path).read_text(encoding="utf-8")
    elif inline:
        text = inline
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        raise SystemExit("error: provide --spec, --inline, or stdin")

    stripped = text.strip()
    if not stripped:
        raise SystemExit("error: empty plan input")
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        data = _parse_yamlish(stripped)
    if not isinstance(data, dict):
        raise SystemExit("error: plan input must be an object")
    return data


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def string_list(stage: dict[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        values.extend(str(item) for item in as_list(stage.get(key)))
    return values


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts if part != "")


def quote_stage_command(command: Any) -> list[str]:
    if isinstance(command, list):
        return [str(part) for part in command]
    if command is None:
        return []
    return [str(command)]


def stage_name(stage: dict[str, Any], index: int) -> str:
    value = stage.get("name") or stage.get("stage")
    if not value:
        raise SystemExit(f"error: stages[{index}] is missing required name")
    return str(value)


def build_stage_add(stage: dict[str, Any], index: int) -> list[str]:
    name = stage_name(stage, index)
    command = quote_stage_command(stage.get("cmd") or stage.get("command"))
    if not command:
        raise SystemExit(f"error: stage {name!r} is missing cmd/command")

    args = ["dvc", "stage", "add", "-n", name]
    if stage.get("force"):
        args.append("--force")
    for dep in string_list(stage, "deps", "dependencies"):
        args.extend(["-d", dep])
    for param in string_list(stage, "params", "parameters"):
        args.extend(["-p", param])
    for out in string_list(stage, "outs", "outputs"):
        args.extend(["-o", out])
    for out in string_list(stage, "outs_no_cache", "outs-no-cache", "outputs_no_cache"):
        args.extend(["-O", out])
    for out in string_list(stage, "outs_persist", "outs-persist"):
        args.extend(["--outs-persist", out])
    for out in string_list(stage, "outs_persist_no_cache", "outs-persist-no-cache"):
        args.extend(["--outs-persist-no-cache", out])
    for metric in string_list(stage, "metrics"):
        args.extend(["-m", metric])
    for metric in string_list(stage, "metrics_no_cache", "metrics-no-cache"):
        args.extend(["-M", metric])
    for plot in string_list(stage, "plots"):
        args.extend(["--plots", plot])
    for plot in string_list(stage, "plots_no_cache", "plots-no-cache"):
        args.extend(["--plots-no-cache", plot])
    if stage.get("wdir"):
        args.extend(["--wdir", str(stage["wdir"])])
    if stage.get("always_changed") or stage.get("always-changed"):
        args.append("--always-changed")
    if stage.get("desc"):
        args.extend(["--desc", str(stage["desc"])])
    if stage.get("run"):
        args.append("--run")
    args.extend(command)
    return args


def collect_outputs(stages: list[dict[str, Any]]) -> list[str]:
    outputs: list[str] = []
    for stage in stages:
        for key in (
            "outs",
            "outputs",
            "outs_no_cache",
            "outs-no-cache",
            "outputs_no_cache",
            "outs_persist",
            "outs-persist",
            "outs_persist_no_cache",
            "outs-persist-no-cache",
            "metrics",
            "metrics_no_cache",
            "metrics-no-cache",
            "plots",
            "plots_no_cache",
            "plots-no-cache",
        ):
            outputs.extend(str(item) for item in as_list(stage.get(key)))
    return sorted(dict.fromkeys(outputs))


def print_plan(data: dict[str, Any], args: argparse.Namespace) -> None:
    raw_stages = data.get("stages", [])
    if not isinstance(raw_stages, list):
        raise SystemExit("error: stages must be a list")
    stages: list[dict[str, Any]] = []
    for index, stage in enumerate(raw_stages):
        if not isinstance(stage, dict):
            raise SystemExit(f"error: stages[{index}] must be an object")
        stages.append(stage)

    title = str(data.get("name") or data.get("pipeline") or "DVC pipeline plan")
    print(f"# {title}")
    print()
    print("This is a dry planning report. No DVC command was executed.")
    print()

    if not stages:
        print("## Stage Commands")
        print("No stages were provided.")
    else:
        print("## Stage Commands")
        for index, stage in enumerate(stages):
            name = stage_name(stage, index)
            print(f"# stage: {name}")
            print(quote_command(build_stage_add(stage, index)))
        print()

    print("## Suggested Read-Only Validation")
    validation = [
        ["dvc", "root"],
        ["dvc", "status"],
        ["dvc", "stage", "list", "--all"],
    ]
    if args.include_dag:
        validation.append(["dvc", "dag"])
    validation.extend(
        [
            ["git", "diff", "--", "dvc.yaml", "dvc.lock"],
            ["git", "status", "--short"],
        ]
    )
    for command in validation:
        print(quote_command(command))
    print()

    dry_targets = [str(target) for target in args.dry_repro]
    dry_targets.extend(str(target) for target in as_list(data.get("dry_repro")))
    if not dry_targets and stages:
        dry_targets = [stage_name(stage, index) for index, stage in enumerate(stages)]
    print("## Dry Reproduction Plan")
    if dry_targets:
        for target in dict.fromkeys(dry_targets):
            print(quote_command(["dvc", "repro", "--dry", target]))
    else:
        print("No dry repro targets were provided.")
    print()

    outputs = collect_outputs(stages)
    print("## Metadata And Output Review")
    print("Review and commit DVC metadata intentionally: dvc.yaml, dvc.lock, .dvcignore, and any generated .dvc files.")
    if outputs:
        print("Declared outputs/metrics/plots:")
        for output in outputs:
            print(f"- {output}")
    else:
        print("No declared outputs, metrics, or plots were found in the plan.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print deterministic dvc stage add and dvc repro --dry plans without executing DVC.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--spec", help="Path to a JSON or simple YAML-ish plan file.")
    source.add_argument("--inline", help="Inline JSON or simple YAML-ish plan text.")
    parser.add_argument(
        "--dry-repro",
        action="append",
        default=[],
        metavar="TARGET",
        help="Target for a planned 'dvc repro --dry' command. May be repeated.",
    )
    parser.add_argument(
        "--include-dag",
        action="store_true",
        help="Include 'dvc dag' in suggested validation commands.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    data = load_spec(args.spec, args.inline)
    print_plan(data, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

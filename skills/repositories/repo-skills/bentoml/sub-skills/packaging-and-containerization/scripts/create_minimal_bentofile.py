#!/usr/bin/env python3
"""Create a minimal BentoML bentofile.yaml without building a Bento."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def dump_simple_yaml(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(dump_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {format_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{prefix}- {{}}")
                    continue
                first_key = next(iter(item))
                first_value = item[first_key]
                if isinstance(first_value, (dict, list)):
                    lines.append(f"{prefix}- {first_key}:")
                    lines.extend(dump_simple_yaml(first_value, indent + 4))
                else:
                    lines.append(f"{prefix}- {first_key}: {format_scalar(first_value)}")
                rest = {key: val for key, val in item.items() if key != first_key}
                lines.extend(dump_simple_yaml(rest, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.extend(dump_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {format_scalar(item)}")
    return lines


def format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def dump_yaml(value: Any) -> str:
    if yaml is not None:
        return yaml.safe_dump(value, sort_keys=False)
    return "\n".join(dump_simple_yaml(value)) + "\n"

SERVICE_RE = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_][\w.]*$")


def parse_key_value(items: list[str], option_name: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        key, separator, value = item.partition("=")
        if not separator or not key:
            raise SystemExit(f"{option_name} entries must use KEY=VALUE: {item!r}")
        parsed[key] = value
    return parsed


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    if not SERVICE_RE.match(args.service):
        raise SystemExit("--service should look like module:object, for example service:MyService")

    config: dict[str, Any] = {"service": args.service}
    if args.name:
        config["name"] = args.name
    if args.description:
        config["description"] = args.description

    labels = parse_key_value(args.label, "--label")
    if labels:
        config["labels"] = labels

    includes = args.include or ["service.py"]
    if includes:
        config["include"] = includes
    if args.exclude:
        config["exclude"] = args.exclude

    python_cfg: dict[str, Any] = {}
    if args.requirements_txt:
        python_cfg["requirements_txt"] = args.requirements_txt
    elif args.package:
        python_cfg["packages"] = args.package
    if args.no_lock:
        python_cfg["lock_packages"] = False
    if args.src_layout:
        python_cfg["is_src_layout"] = True
    if python_cfg:
        config["python"] = python_cfg

    docker_cfg: dict[str, Any] = {}
    if args.python_version:
        docker_cfg["python_version"] = args.python_version
    if args.distro:
        docker_cfg["distro"] = args.distro
    if args.system_package:
        docker_cfg["system_packages"] = args.system_package
    if docker_cfg:
        config["docker"] = docker_cfg

    envs = []
    for env in args.env:
        name, separator, value = env.partition("=")
        if not name:
            raise SystemExit(f"--env entries must be NAME or NAME=VALUE: {env!r}")
        item = {"name": name}
        if separator:
            item["value"] = value
        envs.append(item)
    if envs:
        config["envs"] = envs

    build_args = parse_key_value(args.arg, "--arg")
    if build_args:
        config["args"] = build_args

    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", required=True, help="Service import target such as service:MyService")
    parser.add_argument("--name", help="Optional Bento name")
    parser.add_argument("--description", help="Inline description or file: ./README.md")
    parser.add_argument("--label", action="append", default=[], help="Bento label KEY=VALUE; repeatable")
    parser.add_argument("--include", action="append", default=[], help="Include pattern; repeatable")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude pattern; repeatable")
    parser.add_argument("--package", action="append", default=[], help="Python package requirement; repeatable")
    parser.add_argument("--requirements-txt", help="Path to requirements.txt relative to build context")
    parser.add_argument("--no-lock", action="store_true", help="Set python.lock_packages to false")
    parser.add_argument("--src-layout", action="store_true", help="Set python.is_src_layout to true")
    parser.add_argument("--python-version", default="3.11", help="Docker Python version, default 3.11")
    parser.add_argument("--distro", choices=["debian", "alpine", "ubi8", "amazonlinux"], help="Docker base distro")
    parser.add_argument("--system-package", action="append", default=[], help="System package; repeatable")
    parser.add_argument("--env", action="append", default=[], help="Environment variable NAME or NAME=VALUE; repeatable")
    parser.add_argument("--arg", action="append", default=[], help="Template argument KEY=VALUE; repeatable")
    parser.add_argument("--output", type=Path, help="Write YAML to this path instead of stdout")
    args = parser.parse_args()

    if args.requirements_txt and args.package:
        print("WARN: --requirements-txt is set, so --package entries are omitted", file=sys.stderr)

    config = build_config(args)
    rendered = dump_yaml(config)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

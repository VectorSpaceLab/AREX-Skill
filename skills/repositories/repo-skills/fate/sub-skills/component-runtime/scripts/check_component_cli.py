#!/usr/bin/env python3
"""Safe smoke helper for the FATE component CLI.

This helper only uses help/list/desc/task-schema probes. It does not execute
component jobs and it does not require a live FATE-Flow service.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Sequence


def run_checked(cmd: Sequence[str], label: str) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"{label} failed with exit code {proc.returncode}\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the safe FATE component CLI surface.")
    parser.add_argument(
        "--component",
        default="psi",
        help="sample component name to inspect with desc; default: psi",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=None,
        help="directory for saved probe files; defaults to a temporary directory",
    )
    args = parser.parse_args()

    tempdir = None
    if args.output_dir is None:
        tempdir = tempfile.TemporaryDirectory(prefix="fate-component-cli-")
        output_dir = pathlib.Path(tempdir.name)
    else:
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    top_help = run_checked([sys.executable, "-m", "fate.components", "--help"], "top-level help")
    require("component" in top_help and "test" in top_help, "top-level help did not expose both component and test groups")

    component_help = run_checked(
        [sys.executable, "-m", "fate.components", "component", "--help"],
        "component group help",
    )
    require("artifact-type" in component_help, "component help did not list artifact-type")
    require("task-schema" in component_help, "component help did not list the hyphenated task-schema command")

    list_path = output_dir / "component-list.json"
    desc_path = output_dir / f"{args.component}.yaml"
    schema_path = output_dir / "task-schema.json"
    io_path = output_dir / f"{args.component}-artifact-type.yaml"

    run_checked(
        [sys.executable, "-m", "fate.components", "component", "list", "--save", str(list_path)],
        "component list",
    )
    run_checked(
        [sys.executable, "-m", "fate.components", "component", "desc", "--name", args.component, "--save", str(desc_path)],
        "component desc",
    )
    run_checked(
        [sys.executable, "-m", "fate.components", "component", "task-schema", "--save", str(schema_path)],
        "component task-schema",
    )
    run_checked(
        [
            sys.executable,
            "-m",
            "fate.components",
            "component",
            "artifact-type",
            "--name",
            args.component,
            "--role",
            "guest",
            "--stage",
            "default",
            "--output-path",
            str(io_path),
        ],
        "component artifact-type",
    )

    for path in (list_path, desc_path, schema_path, io_path):
        require(path.exists(), f"expected saved file does not exist: {path}")
        require(path.stat().st_size > 0, f"expected saved file is empty: {path}")

    list_data = json.loads(list_path.read_text())
    require(isinstance(list_data, dict), "list output is not a JSON object")
    require("buildin" in list_data, "list output missing buildin key")
    require("thirdparty" in list_data, "list output missing thirdparty key")
    require(args.component in list_data["buildin"], f"sample component {args.component!r} was not found in the built-in list")

    desc_text = desc_path.read_text()
    desc_lines = desc_text.splitlines()
    require(desc_lines and desc_lines[0].strip() == "component:", "descriptor save output did not start with a component block")
    require(
        any(line.strip() == f"name: {args.component}" for line in desc_lines[:12]),
        "descriptor save output did not contain the requested component name",
    )
    require("schema_version: v1" in desc_text, "descriptor save output did not declare schema_version: v1")

    schema = json.loads(schema_path.read_text())
    require(isinstance(schema, dict), "task schema output is not a JSON object")
    require(schema.get("title") == "TaskConfigSpec", "task schema title was not TaskConfigSpec")
    required = set(schema.get("required", []))
    expected_required = {"task_id", "party_task_id", "task_name", "component", "role", "party_id", "conf"}
    require(expected_required.issubset(required), f"task schema missing required keys: {sorted(expected_required - required)}")
    properties = schema.get("properties", {})
    require(properties.get("stage", {}).get("default") == "default", "task schema stage default was not default")
    definitions = schema.get("definitions", {})
    task_conf = definitions.get("TaskConfSpec", {})
    conf_properties = task_conf.get("properties", {})
    for key in ("device", "computing", "federation", "logger"):
        require(key in conf_properties, f"task schema missing TaskConfSpec property {key!r}")

    io_text = io_path.read_text()
    require("inputs:" in io_text and "outputs:" in io_text, "artifact-type output missing inputs/outputs sections")
    require("path_type:" in io_text, "artifact-type output missing path_type entries")

    print(f"OK: validated component CLI probes for {args.component!r} in {output_dir}")
    if tempdir is None:
        print(f"saved files kept in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

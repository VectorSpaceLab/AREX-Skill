#!/usr/bin/env python3
"""Emit safe Ultralytics train/val/tune command plans without running training."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path

TASKS = ("detect", "segment", "pose", "obb", "classify", "semantic")
MODES = ("train", "val", "tune")


def parse_key_value(items: list[str]) -> dict[str, str]:
    """Parse extra CLI arg=value tokens."""
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item or item.startswith("--"):
            raise argparse.ArgumentTypeError(f"extras must use arg=value syntax, got {item!r}")
        key, value = item.split("=", 1)
        if not key or not value:
            raise argparse.ArgumentTypeError(f"extras must use non-empty arg=value syntax, got {item!r}")
        parsed[key] = value
    return parsed


def shell_join(parts: list[str]) -> str:
    """Return a shell-safe command string."""
    return " ".join(shlex.quote(str(part)) for part in parts)


def python_value(value: str) -> str:
    """Render a simple Python literal for generated API snippets."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered.title()
    if lowered == "none":
        return "None"
    try:
        int(value)
        return value
    except ValueError:
        pass
    try:
        float(value)
        return value
    except ValueError:
        pass
    if "," in value and all(part.strip("-+ ").isdigit() for part in value.split(",") if part):
        return repr([int(part) for part in value.split(",")])
    return repr(value)


def build_args(args: argparse.Namespace) -> dict[str, str]:
    """Build the final Ultralytics arg=value map."""
    values: dict[str, str] = {}
    if args.model:
        values["model"] = args.model
    if args.data:
        values["data"] = args.data

    if args.cpu_tiny:
        defaults = {
            "device": "cpu",
            "imgsz": "32",
            "batch": "1",
            "workers": "0",
            "plots": "False",
        }
        if args.mode == "train":
            defaults["epochs"] = "1"
        if args.mode == "tune":
            defaults.update({"epochs": "1", "iterations": "2"})
        values = {**defaults, **values}

    for key in ("epochs", "imgsz", "batch", "device", "workers", "project", "name"):
        value = getattr(args, key)
        if value is not None:
            values[key] = str(value)

    if args.no_plots:
        values["plots"] = "False"
    if args.resume:
        values["resume"] = "True"
    values.update(parse_key_value(args.extra or []))
    return values


def build_cli(args: argparse.Namespace, values: dict[str, str]) -> list[str] | None:
    """Build the planned yolo CLI command, when the workflow has a direct CLI mode."""
    if args.mode == "tune":
        return None
    command = [args.executable]
    if args.task:
        command.append(args.task)
    command.append(args.mode)
    command.extend(f"{key}={value}" for key, value in values.items() if key != "iterations")
    return command


def build_python(args: argparse.Namespace, values: dict[str, str]) -> str:
    """Build the planned Python API snippet."""
    model = values.get("model", args.model or "yolo26n.pt")
    call_values = {key: value for key, value in values.items() if key != "model"}
    if args.mode != "tune":
        kwargs = ", ".join(f"{key}={python_value(value)}" for key, value in call_values.items())
        return "\n".join([
            "from ultralytics import YOLO",
            "",
            f"model = YOLO({model!r})",
            f"metrics = model.{args.mode}({kwargs})" if kwargs else f"metrics = model.{args.mode}()",
        ])

    iterations = int(values.get("iterations", args.iterations))
    tune_values = {key: value for key, value in call_values.items() if key != "iterations"}
    kwargs = ", ".join(f"{key}={python_value(value)}" for key, value in tune_values.items())
    if kwargs:
        kwargs = ", " + kwargs
    return "\n".join([
        "from ultralytics import YOLO",
        "",
        f"model = YOLO({model!r})",
        f"model.tune(iterations={iterations}{kwargs})",
    ])


def side_effect_warnings(args: argparse.Namespace, values: dict[str, str]) -> list[str]:
    """Summarize likely side effects without inspecting the environment."""
    warnings = ["Plan only: this script does not import Ultralytics or run training/validation."]
    model = values.get("model")
    data = values.get("data")
    if model and not Path(model).exists() and model.endswith(".pt"):
        warnings.append("Named model weights may download if not already cached.")
    if data and not Path(data).exists() and (data.endswith(".yaml") or data.startswith(("http://", "https://"))):
        warnings.append("Named or remote data may download or require network access.")
    if args.mode in {"train", "tune"}:
        warnings.append("Training writes run directories, args.yaml, and checkpoint weights unless save behavior is changed.")
    if args.mode == "val":
        warnings.append("Validation may write plots, labels, or predictions JSON depending on arguments.")
    if args.mode == "tune":
        iterations = int(values.get("iterations", args.iterations))
        epochs = values.get("epochs", "default")
        warnings.append(f"Tuning schedules {iterations} trial(s); each trial trains for epochs={epochs}.")
    if str(values.get("device", "")).replace(" ", "") in {"0,1", "0,1,2", "0,1,2,3", "-1,-1"}:
        warnings.append("Multi-GPU training can spawn distributed subprocesses.")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan safe Ultralytics yolo train/val/tune commands without executing them.",
        epilog="Extra options must use arg=value syntax, for example optimizer=SGD patience=5.",
    )
    parser.add_argument("--mode", choices=MODES, required=True, help="Workflow to plan: train, val, or tune.")
    parser.add_argument("--task", choices=TASKS, default="detect", help="Ultralytics task for the CLI command.")
    parser.add_argument("--model", default="yolo26n.pt", help="Model checkpoint/name/YAML to include in the plan.")
    parser.add_argument("--data", help="Dataset YAML/name/path to include in the plan.")
    parser.add_argument("--cpu-tiny", action="store_true", help="Apply safe CPU/tiny defaults.")
    parser.add_argument("--epochs", type=int, help="Training epochs to plan.")
    parser.add_argument("--iterations", type=int, default=10, help="Tuning iterations for Python tune plans.")
    parser.add_argument("--imgsz", type=int, help="Image size to plan.")
    parser.add_argument("--batch", help="Batch size to plan, including -1 for auto-batch where appropriate.")
    parser.add_argument("--device", help="Device such as cpu, mps, 0, 0,1, -1, or -1,-1.")
    parser.add_argument("--workers", type=int, help="DataLoader worker count to plan.")
    parser.add_argument("--project", help="Output project directory argument to include.")
    parser.add_argument("--name", help="Output run name argument to include.")
    parser.add_argument("--resume", action="store_true", help="Plan resume=True for train/tune API usage.")
    parser.add_argument("--no-plots", action="store_true", help="Include plots=False in the plan.")
    parser.add_argument("--executable", default="yolo", help="CLI executable to show, usually yolo or ultralytics.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON plan instead of text.")
    parser.add_argument("extra", nargs="*", help="Additional Ultralytics arg=value pairs.")
    args = parser.parse_args()

    values = build_args(args)
    command = build_cli(args, values)
    python_snippet = build_python(args, values)
    warnings = side_effect_warnings(args, values)
    plan = {
        "mode": args.mode,
        "task": args.task,
        "cli": shell_join(command) if command else None,
        "python": python_snippet,
        "args": values,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    print("CLI plan:")
    print(plan["cli"] or "No direct yolo CLI tune mode is planned; use the Python API plan.")
    print("\nPython API plan:")
    print(python_snippet)
    print("\nWarnings:")
    for warning in warnings:
        print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

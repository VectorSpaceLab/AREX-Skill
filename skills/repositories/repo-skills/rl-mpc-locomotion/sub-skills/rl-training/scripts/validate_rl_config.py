#!/usr/bin/env python3
"""Safely validate RL task overrides and checkpoint paths.

This helper performs no Isaac Gym import, GPU allocation, training, simulation,
network access, or checkpoint deserialization. It validates the public command
plan before a potentially expensive run.

Examples:
  python validate_rl_config.py --task Aliengo --num-envs 1
  python validate_rl_config.py --task Go1 --test --checkpoint /path/to/user/checkpoints/Go1/model_100.pt
  python validate_rl_config.py --override task=A1 --override headless=True
"""

from __future__ import print_function

import argparse
import json
import os
import re
import sys

TASKS = ("A1", "Aliengo", "Go1")
BOOL_KEYS = {"headless", "test", "torch_deterministic", "multi_gpu", "capture_video", "force_render"}
INT_KEYS = {"num_envs", "seed", "max_iterations", "graphics_device_id", "num_threads", "solver_type", "num_subscenes"}
PATH_KEYS = {"checkpoint"}
ENUM_KEYS = {
    "pipeline": {"cpu", "gpu"},
    "physics_engine": {"physx", "flex"},
}
DEVICE_KEYS = {"sim_device", "rl_device"}
KNOWN_KEYS = (
    {"task", "task_name"}
    | BOOL_KEYS
    | INT_KEYS
    | PATH_KEYS
    | set(ENUM_KEYS)
    | DEVICE_KEYS
)
DEVICE_RE = re.compile(r"^(?:cpu|cuda|gpu)(?::[0-9]+)?$")


def parse_bool(value, key):
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError("{} must be True or False, got {!r}".format(key, value))
    return normalized == "true"


def parse_int(value, key, positive=False):
    if value == "":
        return None
    try:
        number = int(value)
    except ValueError:
        raise ValueError("{} must be an integer, got {!r}".format(key, value))
    if positive and number <= 0:
        raise ValueError("{} must be greater than zero, got {}".format(key, number))
    return number


def validate_pair(key, value, result):
    if not key:
        raise ValueError("override key is empty")
    if key not in KNOWN_KEYS:
        raise ValueError(
            "unsupported top-level override {!r}; use the documented Hydra keys or validate nested task values in the resolved config".format(key)
        )

    if key in {"task", "task_name"}:
        if value not in TASKS:
            raise ValueError("{} must be one of {}, got {!r}".format(key, ", ".join(TASKS), value))
        result[key] = value
    elif key in BOOL_KEYS:
        result[key] = parse_bool(value, key)
    elif key in INT_KEYS:
        result[key] = parse_int(key=key, value=value, positive=key in {"num_envs", "max_iterations"})
    elif key in PATH_KEYS:
        result[key] = value
    elif key in ENUM_KEYS:
        if value not in ENUM_KEYS[key]:
            raise ValueError("{} must be one of {}, got {!r}".format(key, ", ".join(sorted(ENUM_KEYS[key])), value))
        result[key] = value
    elif key in DEVICE_KEYS:
        if not DEVICE_RE.match(value):
            raise ValueError("{} must look like cpu, cuda:0, or gpu:0, got {!r}".format(key, value))
        result[key] = value


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate RL Hydra task/override plans without importing Isaac Gym or loading checkpoints."
    )
    parser.add_argument("--task", choices=TASKS, default="Aliengo", help="robot task name")
    parser.add_argument("--num-envs", type=int, help="positive vectorized environment count")
    parser.add_argument("--checkpoint", help="checkpoint path; checked for existence only")
    parser.add_argument("--test", action="store_true", help="mark the plan as evaluation")
    parser.add_argument("--headless", action="store_true", help="mark the plan as headless")
    parser.add_argument("--max-iterations", type=int, help="positive PPO update count")
    parser.add_argument("--seed", type=int, help="seed; -1 is allowed by the training utility")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="validate a documented top-level Hydra override; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", help="emit the result as JSON")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    errors = []
    warnings = []
    values = {
        "task": args.task,
        "num_envs": args.num_envs,
        "checkpoint": args.checkpoint,
        "test": args.test,
        "headless": args.headless,
        "max_iterations": args.max_iterations,
        "seed": args.seed,
    }

    if args.num_envs is not None and args.num_envs <= 0:
        errors.append("--num-envs must be greater than zero")
    if args.max_iterations is not None and args.max_iterations <= 0:
        errors.append("--max-iterations must be greater than zero")

    for raw in args.override:
        if "=" not in raw:
            errors.append("override must use KEY=VALUE syntax: {!r}".format(raw))
            continue
        key, value = raw.split("=", 1)
        try:
            validate_pair(key.strip(), value.strip(), values)
        except ValueError as exc:
            errors.append(str(exc))

    task = values.get("task_name", values.get("task", "Aliengo"))
    if values.get("task") and values.get("task_name") and values["task"] != values["task_name"]:
        errors.append("task and task_name disagree: {} versus {}".format(values["task"], values["task_name"]))
    if task not in TASKS:
        errors.append("task must be one of {}".format(", ".join(TASKS)))

    checkpoint = values.get("checkpoint")
    checkpoint_info = None
    if checkpoint:
        expanded = os.path.abspath(os.path.expanduser(checkpoint))
        checkpoint_info = {"path": checkpoint, "absolute_path": expanded}
        if not os.path.exists(expanded):
            errors.append("checkpoint does not exist: {}".format(checkpoint))
        elif not os.path.isfile(expanded):
            errors.append("checkpoint is not a regular file: {}".format(checkpoint))
        elif os.path.getsize(expanded) == 0:
            errors.append("checkpoint is empty: {}".format(checkpoint))
    elif values.get("test"):
        warnings.append("test=True without checkpoint relies on latest-run fallback under the configured task run root; use an explicit file for reproducibility")

    if not values.get("test") and checkpoint:
        warnings.append("checkpoint is supplied with test=False: the run will load it and continue training, not evaluate only")

    result = {
        "valid": not errors,
        "task": task,
        "values": values,
        "checkpoint": checkpoint_info,
        "warnings": warnings,
        "errors": errors,
        "backend_note": "This check does not prove Isaac Gym, CUDA, repository imports, or checkpoint compatibility.",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print("{}: RL configuration plan".format(status))
        print("  task: {}".format(task))
        print("  num_envs: {}".format(values.get("num_envs") if values.get("num_envs") is not None else "default (32)"))
        print("  mode: {}".format("evaluation" if values.get("test") else "training/resume"))
        if checkpoint_info:
            print("  checkpoint: {} (path only; not deserialized)".format(checkpoint_info["path"]))
        for warning in warnings:
            print("WARNING: {}".format(warning))
        for error in errors:
            print("ERROR: {}".format(error))
        print("NOTE: {}".format(result["backend_note"]))

    return 0 if result["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())

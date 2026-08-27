#!/usr/bin/env python3
"""Validate project config, robot assets, checkpoints, and device intent.

The validator is read-only. It resolves paths against the project root rather
than the caller's current directory, so it is safe to run from any directory.
It does not import Isaac Gym or launch Hydra.
"""
from __future__ import print_function

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

TASKS = {
    "Aliengo": "assets/aliengo_description/urdf/aliengo.urdf",
    "A1": "assets/a1_description/urdf/a1.urdf",
    "Go1": "assets/go1_description/urdf/go1.urdf",
}
REQUIRED_CONFIG_KEYS = (
    "task_name", "physics_engine", "pipeline", "sim_device", "rl_device",
    "graphics_device_id", "num_threads", "solver_type", "num_subscenes",
    "headless", "defaults",
)
MARKERS = ("RL_Environment", "assets", "MPC_Controller")


def emit(label, state, detail):
    print("[%s] %-22s %s" % (state, label, detail))


def find_root(value, config_value=None):
    if value:
        root = Path(value).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("--repo-root is not a directory: %s" % value)
        return root
    candidates = []
    if config_value:
        config_path = Path(config_value).expanduser().resolve()
        candidates.extend((config_path.parent,) + tuple(config_path.parent.parents))
    candidates.extend((Path.cwd(),) + tuple(Path.cwd().parents))
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if all((candidate / marker).exists() for marker in MARKERS):
            return candidate
    return None


def relative_display(path, root):
    if root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is unavailable; install the environment.yml dependency before validating YAML")
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("top-level YAML value is not a mapping")
    return value


def validate_urdf(asset_path, root):
    failures = 0
    try:
        text = asset_path.read_text(encoding="utf-8")
    except Exception as error:
        emit("asset read", "FAIL", str(error).splitlines()[0])
        return 1
    filenames = re.findall(r'<mesh\s+filename=["\']([^"\']+)', text)
    if not filenames:
        emit("mesh references", "WARN", "no URDF mesh elements found")
        return 0
    checked = set()
    for filename in filenames:
        if filename.startswith("package://"):
            filename = filename[len("package://"):]
            parts = filename.split("/", 1)
            filename = parts[1] if len(parts) == 2 else parts[0]
        candidate = asset_path.parent.parent / filename
        checked.add(filename)
        if candidate.is_file():
            continue
        failures += 1
        emit("asset mesh", "FAIL", "%s is missing" % filename)
    state = "PASS" if failures == 0 else "FAIL"
    emit("mesh references", state, "%d referenced mesh file(s) checked" % len(checked))
    return failures


def check_device(device, strict):
    if not isinstance(device, str) or not device.startswith("cuda"):
        emit("configured device", "INFO", "%s (CPU or non-CUDA intent)" % device)
        return 0
    try:
        import torch
        available = bool(torch.cuda.is_available())
        detail = "%s; torch CUDA available=%s" % (device, available)
        emit("configured device", "PASS" if available else "BLOCKED", detail)
        return 0 if available or not strict else 1
    except Exception as error:
        emit("configured device", "BLOCKED", "cannot probe torch CUDA: %s" % str(error).splitlines()[0])
        return 1 if strict else 0


def validate_task(root, task):
    failures = 0
    if root is None:
        emit("task config", "INFO", "%s not checked; pass --repo-root /path/to/current/project-copy for task and asset validation" % task)
        return failures
    task_path = root / "RL_Environment" / "cfg" / "task" / (task + ".yaml")
    if not task_path.is_file():
        emit("task config", "FAIL", "%s is missing" % relative_display(task_path, root))
        return 1
    try:
        task_cfg = load_yaml(task_path)
    except Exception as error:
        emit("task config", "FAIL", "%s" % str(error).splitlines()[0])
        return 1
    if task_cfg.get("name") != task:
        failures += 1
        emit("task name", "FAIL", "declares %r, expected %r" % (task_cfg.get("name"), task))
    else:
        emit("task config", "PASS", "%s" % relative_display(task_path, root))
    if "env" not in task_cfg or "sim" not in task_cfg:
        failures += 1
        emit("task sections", "FAIL", "env and sim mappings are required")
    asset_relative = TASKS.get(task)
    if asset_relative:
        asset_path = root / asset_relative
        if asset_path.is_file():
            emit("robot asset", "PASS", asset_relative)
            failures += validate_urdf(asset_path, root)
        else:
            failures += 1
            emit("robot asset", "FAIL", "%s is missing" % asset_relative)
    return failures


def validate_checkpoint(root, value, required):
    if not value:
        emit("checkpoint", "INFO", "not supplied; training or latest-run fallback remains possible")
        return 0
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (root or Path.cwd()) / path
    if path.is_file():
        emit("checkpoint", "PASS", relative_display(path, root))
        return 0
    state = "FAIL" if required else "WARN"
    emit("checkpoint", state, "%s does not exist" % relative_display(path, root))
    return 1 if required else 0


def main():
    parser = argparse.ArgumentParser(description="Read-only validation for project configs, assets, devices, and checkpoints.")
    parser.add_argument("--repo-root", help="current project root for optional layout/asset integrity checks; otherwise discover it")
    parser.add_argument("--config", help="YAML config path; absolute paths are preferred when no project copy is supplied")
    parser.add_argument("--task", choices=sorted(TASKS), default="Aliengo", help="task config and matching robot asset")
    parser.add_argument("--all-tasks", action="store_true", help="validate all bundled A1, Aliengo, and Go1 task/asset pairs")
    parser.add_argument("--checkpoint", help="checkpoint path, relative to the project root unless absolute")
    parser.add_argument("--require-checkpoint", action="store_true", help="fail when --checkpoint is absent or missing")
    parser.add_argument("--strict-device", action="store_true", help="fail when a configured CUDA device is unavailable")
    parser.add_argument("--strict", action="store_true", help="return 2 for any validation failure")
    args = parser.parse_args()

    try:
        root = find_root(args.repo_root, args.config)
    except ValueError as error:
        emit("repository root", "FAIL", str(error))
        return 2
    if root is None:
        emit("repository root", "INFO", "current project copy not supplied; package diagnostics do not require one")
        if not args.config:
            emit("main config", "INFO", "not checked; pass --config /path/to/config.yaml or --repo-root /path/to/current/project-copy")
            if args.strict:
                print("Configuration gate: FAILED (no config or current project copy supplied).")
                return 2
            print("Configuration gate: ADVISORY; supply a current config for YAML and asset validation.")
            return 0

    config_path = Path(args.config).expanduser() if args.config else Path("RL_Environment/cfg/config.yaml")
    if not config_path.is_absolute():
        config_path = (root or Path.cwd()) / config_path
    failures = 0
    if not config_path.is_file():
        emit("main config", "FAIL", "%s is missing" % relative_display(config_path, root))
        if args.strict:
            return 2
        print("Configuration gate: ADVISORY failures reported; provide a current config and retry with --strict.")
        return 0
    if root is not None:
        emit("repository root", "PASS", "project markers found")
    try:
        config = load_yaml(config_path)
        emit("main config", "PASS", relative_display(config_path, root))
    except Exception as error:
        emit("main config", "FAIL", str(error).splitlines()[0])
        return 2

    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    if missing:
        failures += len(missing)
        emit("config keys", "FAIL", "missing: %s" % ", ".join(missing))
    else:
        emit("config keys", "PASS", "%d required keys present" % len(REQUIRED_CONFIG_KEYS))

    failures += check_device(config.get("sim_device"), args.strict_device)
    if args.all_tasks:
        for task in sorted(TASKS):
            failures += validate_task(root, task)
    else:
        failures += validate_task(root, args.task)
    failures += validate_checkpoint(root, args.checkpoint, args.require_checkpoint)

    if failures and args.strict:
        print("Configuration gate: FAILED (%d issue(s))." % failures)
        return 2
    if failures:
        print("Configuration gate: ADVISORY failures reported; see troubleshooting.md.")
        return 0
    print("Configuration gate: PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

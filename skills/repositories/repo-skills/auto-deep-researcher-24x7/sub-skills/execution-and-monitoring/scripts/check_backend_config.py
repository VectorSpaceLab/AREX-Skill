#!/usr/bin/env python3
"""Read-only execution configuration and workspace-path validator.

This tool loads YAML with safe_load and performs no network calls, subprocess
launches, scheduler submissions, or writes. Exit 0 means no errors; exit 1
means the configuration or path check is invalid; exit 2 is a usage/dependency
error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _nonempty(mapping: dict[str, Any], key: str, errors: list[str]) -> None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        _error(errors, f"execution.{key} must be a non-empty string")


def _validate_execution(execution: Any, errors: list[str], warnings: list[str]) -> str:
    if execution is None:
        execution = {}
    if not isinstance(execution, dict):
        _error(errors, "execution must be a mapping")
        return "local"

    mode = execution.get("mode", "local")
    if mode not in {"local", "ssh", "slurm"}:
        _error(errors, f"execution.mode must be local, ssh, or slurm (got {mode!r})")
        return str(mode)

    if mode in {"ssh", "slurm"}:
        _nonempty(execution, "ssh_host", errors)
        _nonempty(execution, "remote_workspace", errors)
        remote_python = execution.get("remote_python", "python3")
        if not isinstance(remote_python, str) or not remote_python.strip():
            _error(errors, "execution.remote_python must be a non-empty string")
        ssh_args = execution.get("ssh_args", [])
        if not isinstance(ssh_args, list) or not all(isinstance(x, str) for x in ssh_args):
            _error(errors, "execution.ssh_args must be a list of strings")

    if mode == "slurm":
        _nonempty(execution, "slurm_partition", errors)
        _nonempty(execution, "slurm_time", errors)
        gpu_count = execution.get("slurm_gpus_per_job", 1)
        if gpu_count is not None and (isinstance(gpu_count, bool) or not isinstance(gpu_count, int) or gpu_count < 0):
            _error(errors, "execution.slurm_gpus_per_job must be an integer >= 0 or null")
        for key in ("slurm_gres", "slurm_qos", "slurm_account", "slurm_setup"):
            if key in execution and not isinstance(execution[key], str):
                _error(errors, f"execution.{key} must be a string")
        extra = execution.get("slurm_extra_sbatch", [])
        if not isinstance(extra, list) or not all(isinstance(x, str) for x in extra):
            _error(errors, "execution.slurm_extra_sbatch must be a list of strings")
        grace = execution.get("slurm_unknown_grace_polls", 4)
        if isinstance(grace, bool) or not isinstance(grace, int) or grace < 0:
            _error(errors, "execution.slurm_unknown_grace_polls must be an integer >= 0")
        buffer_seconds = execution.get("slurm_time_buffer", 1800)
        if isinstance(buffer_seconds, bool) or not isinstance(buffer_seconds, int) or buffer_seconds < 0:
            _error(errors, "execution.slurm_time_buffer must be an integer >= 0")
        if execution.get("slurm_setup"):
            warnings.append("slurm_setup is trusted shell text; keep it operator-controlled")
        if extra:
            warnings.append("slurm_extra_sbatch contains trusted scheduler directives")

    return mode


def _validate_monitor(monitor: Any, errors: list[str]) -> None:
    if monitor is None:
        return
    if not isinstance(monitor, dict):
        _error(errors, "monitor must be a mapping")
        return
    poll = monitor.get("poll_interval", 900)
    if isinstance(poll, bool) or not isinstance(poll, int) or poll < 0:
        _error(errors, "monitor.poll_interval must be an integer >= 0")
    for key in ("zero_llm", "notify_on_complete"):
        if key in monitor and not isinstance(monitor[key], bool):
            _error(errors, f"monitor.{key} must be boolean")


def _normalize_relative(raw: str) -> str:
    if raw is None or not str(raw).strip():
        raise ValueError("path cannot be empty")
    pure = PurePosixPath(str(raw))
    if pure.is_absolute():
        raise ValueError("path must be relative to workspace")
    if any(part == ".." for part in pure.parts):
        raise ValueError("path escapes workspace")
    normalized = str(pure)
    return "." if normalized in {"", "."} else normalized


def _validate_path(root_text: str, raw_path: str) -> dict[str, str]:
    root = Path(root_text).expanduser().resolve(strict=False)
    normalized = _normalize_relative(raw_path)
    parts = [part for part in PurePosixPath(normalized).parts if part not in {"", "."}]
    candidate = (root / Path(*parts)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes workspace through a symlink") from exc
    return {"root": str(root), "path": normalized, "resolved": str(candidate)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate execution YAML and a workspace-relative path without side effects")
    parser.add_argument("--config", required=True, help="YAML configuration to read")
    parser.add_argument("--workspace-root", help="Workspace root for an optional path check")
    parser.add_argument("--path", help="Relative path for an optional path check")
    args = parser.parse_args(argv)

    errors: list[str] = []
    warnings: list[str] = []
    try:
        import yaml
    except ImportError:
        print(json.dumps({"ok": False, "errors": ["PyYAML is required to read --config"]}, indent=2))
        return 2

    try:
        config = yaml.safe_load(Path(args.config).read_text())
    except FileNotFoundError:
        errors.append(f"config file not found: {args.config}")
        config = {}
    except OSError as exc:
        errors.append(f"cannot read config: {exc}")
        config = {}
    except yaml.YAMLError as exc:
        errors.append(f"invalid YAML: {exc}")
        config = {}

    if config is None:
        config = {}
    if not isinstance(config, dict):
        errors.append("config root must be a mapping")
        config = {}

    mode = _validate_execution(config.get("execution", {}), errors, warnings)
    _validate_monitor(config.get("monitor", {}), errors)

    if (args.workspace_root is None) != (args.path is None):
        errors.append("--workspace-root and --path must be supplied together")
    path_result = None
    if args.workspace_root is not None and args.path is not None:
        try:
            path_result = _validate_path(args.workspace_root, args.path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))

    result: dict[str, Any] = {"ok": not errors, "mode": mode, "warnings": warnings}
    if path_result is not None:
        result["path_check"] = path_result
    if errors:
        result["errors"] = errors
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

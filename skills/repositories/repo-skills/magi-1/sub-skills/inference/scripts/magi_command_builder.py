#!/usr/bin/env python3
"""Print safe MAGI source-code inference commands.

This helper only builds shell text. It does not execute inference, import MAGI,
load checkpoints, or touch CUDA state.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a MAGI source-code CLI command for t2v, i2v, or v2v plus "
            "recommended environment variables. No command is executed."
        )
    )
    parser.add_argument("--config-file", required=True, help="MAGI config JSON to pass to --config_file.")
    parser.add_argument("--mode", required=True, choices=("t2v", "i2v", "v2v"), help="Inference mode.")
    parser.add_argument("--prompt", required=True, help="Prompt text to pass to --prompt.")
    parser.add_argument("--output-path", required=True, help="Destination MP4 path to pass to --output_path.")
    parser.add_argument("--image-path", help="Input image path; required for --mode i2v.")
    parser.add_argument("--prefix-video-path", help="Input prefix video path; required for --mode v2v.")
    parser.add_argument(
        "--launcher",
        choices=("auto", "python", "torchrun"),
        default="auto",
        help="Launcher to print. auto uses torchrun when config pp_size*cp_size or --nproc-per-node is >1.",
    )
    parser.add_argument(
        "--nproc-per-node",
        type=int,
        default=None,
        help="torchrun processes per node. Defaults to config pp_size*cp_size when readable, else 1.",
    )
    parser.add_argument("--nnodes", type=int, default=1, help="torchrun --nnodes value. Default: 1.")
    parser.add_argument(
        "--rdzv-endpoint",
        default="localhost:6009",
        help="torchrun rendezvous endpoint and single-process MASTER_ADDR/MASTER_PORT source. Default: localhost:6009.",
    )
    parser.add_argument("--python-executable", default="python3", help="Python executable for single-process command.")
    parser.add_argument(
        "--entrypoint",
        default="inference/pipeline/entry.py",
        help="Source-code inference entry point. Default: inference/pipeline/entry.py.",
    )
    parser.add_argument(
        "--extra-env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional environment export to include. May be passed multiple times.",
    )
    parser.add_argument(
        "--skip-config-check-line",
        action="store_true",
        help="Do not print the suggested magi_config_check.py preflight line.",
    )
    return parser.parse_args()


def read_expected_world_size(config_file: str) -> tuple[int | None, list[str], dict[str, Any]]:
    warnings: list[str] = []
    summary: dict[str, Any] = {}
    try:
        with Path(config_file).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - preflight should keep building a command.
        warnings.append(f"Could not read config for process-count inference: {exc}")
        return None, warnings, summary

    engine = data.get("engine_config") if isinstance(data, dict) else None
    if not isinstance(engine, dict):
        warnings.append("Config has no engine_config object; defaulting process count to 1.")
        return None, warnings, summary

    pp_size = engine.get("pp_size")
    cp_size = engine.get("cp_size")
    if not isinstance(pp_size, int) or isinstance(pp_size, bool) or pp_size <= 0:
        warnings.append("engine_config.pp_size is missing or invalid; defaulting process count to 1.")
        return None, warnings, summary
    if not isinstance(cp_size, int) or isinstance(cp_size, bool) or cp_size <= 0:
        warnings.append("engine_config.cp_size is missing or invalid; defaulting process count to 1.")
        return None, warnings, summary

    summary["pp_size"] = pp_size
    summary["cp_size"] = cp_size
    summary["cp_strategy"] = engine.get("cp_strategy")
    summary["distill"] = engine.get("distill")
    summary["fp8_quant"] = engine.get("fp8_quant")
    return pp_size * cp_size, warnings, summary


def endpoint_to_master(endpoint: str) -> tuple[str, str]:
    if ":" in endpoint:
        host, port = endpoint.rsplit(":", 1)
        return host or "localhost", port or "6009"
    return endpoint or "localhost", "6009"


def shell_join(parts: list[str]) -> str:
    return shlex.join(str(part) for part in parts)


def validate_mode_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.mode == "i2v" and not args.image_path:
        errors.append("--image-path is required when --mode i2v.")
    if args.mode == "v2v" and not args.prefix_video_path:
        errors.append("--prefix-video-path is required when --mode v2v.")
    if args.mode == "t2v" and (args.image_path or args.prefix_video_path):
        errors.append("--mode t2v does not use --image-path or --prefix-video-path.")
    if args.nproc_per_node is not None and args.nproc_per_node <= 0:
        errors.append("--nproc-per-node must be > 0.")
    if args.nnodes <= 0:
        errors.append("--nnodes must be > 0.")
    for item in args.extra_env:
        if "=" not in item or item.startswith("="):
            errors.append(f"--extra-env must be KEY=VALUE, got: {item}")
    return errors


def build_entry_args(args: argparse.Namespace) -> list[str]:
    entry_args = [
        args.entrypoint,
        "--config_file",
        args.config_file,
        "--mode",
        args.mode,
        "--prompt",
        args.prompt,
        "--output_path",
        args.output_path,
    ]
    if args.mode == "i2v":
        entry_args.extend(["--image_path", args.image_path])
    if args.mode == "v2v":
        entry_args.extend(["--prefix_video_path", args.prefix_video_path])
    return entry_args


def build_env_exports(launcher: str, nproc: int, endpoint: str, extra_env: list[str]) -> list[tuple[str, str]]:
    env: list[tuple[str, str]] = [
        ("PAD_HQ", "1"),
        ("PAD_DURATION", "1"),
        ("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True"),
        ("OFFLOAD_T5_CACHE", "true"),
        ("OFFLOAD_VAE_CACHE", "true"),
    ]
    if launcher == "python":
        master_addr, master_port = endpoint_to_master(endpoint)
        env.extend(
            [
                ("MASTER_ADDR", master_addr),
                ("MASTER_PORT", master_port),
                ("WORLD_SIZE", str(nproc)),
                ("RANK", "0"),
            ]
        )
    if launcher == "torchrun" or nproc > 1:
        env.extend(
            [
                ("CUDA_DEVICE_MAX_CONNECTIONS", "1"),
                ("NCCL_ALGO", "^NVLS"),
            ]
        )
    env.append(("PYTHONPATH", "$PWD:${PYTHONPATH:-}"))
    for item in extra_env:
        key, value = item.split("=", 1)
        env.append((key, value))
    return env


def export_line(key: str, value: str) -> str:
    if value == "$PWD:${PYTHONPATH:-}":
        return f"export {key}=\"{value}\""
    return f"export {key}={shlex.quote(value)}"


def main() -> int:
    args = parse_args()
    errors = validate_mode_args(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    expected_world_size, warnings, config_summary = read_expected_world_size(args.config_file)
    nproc = args.nproc_per_node or expected_world_size or 1

    if args.launcher == "auto":
        launcher = "torchrun" if nproc > 1 else "python"
    else:
        launcher = args.launcher

    if launcher == "python" and nproc != 1:
        warnings.append("Python launcher with nproc != 1 will not spawn multiple ranks; use --launcher torchrun.")
    if launcher == "torchrun" and nproc < 1:
        warnings.append("torchrun process count should be at least 1.")
    if expected_world_size is not None and nproc != expected_world_size:
        warnings.append(f"nproc_per_node={nproc} does not match config pp_size*cp_size={expected_world_size}.")

    entry_args = build_entry_args(args)
    env_exports = build_env_exports(launcher, nproc, args.rdzv_endpoint, args.extra_env)

    if launcher == "torchrun":
        command = shell_join(
            [
                "torchrun",
                "--rdzv-backend=c10d",
                f"--rdzv-endpoint={args.rdzv_endpoint}",
                f"--nnodes={args.nnodes}",
                f"--nproc_per_node={nproc}",
                *entry_args,
            ]
        )
    else:
        command = shell_join([args.python_executable, *entry_args])

    print("# MAGI source-code inference command (not executed by this helper)")
    print(f"# Mode: {args.mode}")
    if config_summary:
        details = ", ".join(f"{key}={value}" for key, value in config_summary.items())
        print(f"# Config summary: {details}")
    if expected_world_size is not None:
        print(f"# Config expects WORLD_SIZE={expected_world_size} from pp_size*cp_size.")
    if warnings:
        print("# Warnings:")
        for warning in warnings:
            print(f"# - {warning}")
    print("cd <magi-source-root>")
    if not args.skip_config_check_line:
        check_line = ["python3", "<inference-skill>/scripts/magi_config_check.py", args.config_file]
        if expected_world_size is not None:
            check_line.extend(["--world-size", str(nproc)])
        print("# Suggested preflight:")
        print(shell_join(check_line))
    print("# Recommended environment:")
    for key, value in env_exports:
        print(export_line(key, value))
    print("# Command:")
    print(command)
    print("# Note: this is only a command builder. Full generation requires valid MAGI DiT, T5, VAE, and special-token assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

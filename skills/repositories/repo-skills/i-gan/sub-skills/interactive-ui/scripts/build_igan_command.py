#!/usr/bin/env python3
"""Build a dry-run launch command for the legacy iGAN PyQt4 UI.

This helper adapts the iGAN_main.py command-line contract into a safe command
builder. It does not import iGAN, PyQt4, Theano, OpenCV, qdarkstyle, or CUDA; it
only formats the environment and argv that a user may run later in a compatible
legacy checkout.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Dict, List, Tuple


def positive_int(value: str) -> int:
    """Argparse type for positive integers."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def nonnegative_float(value: str) -> float:
    """Argparse type for non-negative floats."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected float, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected a non-negative float")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a dry-run shell command for launching iGAN_main.py without "
            "opening PyQt4, loading Theano, touching CUDA, or downloading files."
        )
    )
    parser.add_argument("--model-name", "--model_name", dest="model_name", default="outdoor_64",
                        help="model name passed to iGAN_main.py (default: outdoor_64)")
    parser.add_argument("--model-type", "--model_type", dest="model_type", default="dcgan_theano",
                        help="model type / file suffix passed to iGAN_main.py (default: dcgan_theano)")
    parser.add_argument("--framework", default="theano",
                        help="optimizer framework suffix for constrained_opt_<framework> (default: theano)")
    parser.add_argument("--win-size", "--win_size", dest="win_size", type=positive_int, default=384,
                        help="main window size in pixels; iGAN rounds down to a multiple of 4 (default: 384)")
    parser.add_argument("--batch-size", "--batch_size", dest="batch_size", type=positive_int, default=64,
                        help="number of latent candidates optimized per edit (default: 64)")
    parser.add_argument("--n-iters", "--n_iters", dest="n_iters", type=positive_int, default=40,
                        help="optimization iterations per edit (default: 40)")
    parser.add_argument("--top-k", "--top_k", dest="top_k", type=positive_int, default=16,
                        help="maximum candidate thumbnails shown (default: 16)")
    parser.add_argument("--morph-steps", "--morph_steps", dest="morph_steps", type=positive_int, default=16,
                        help="interpolation frames for slider/playback (default: 16)")
    parser.add_argument("--model-file", "--model_file", dest="model_file", default=None,
                        help="explicit model file path; default is ./models/<model_name>.<model_type>")
    parser.add_argument("--d-weight", "--d_weight", dest="d_weight", type=nonnegative_float, default=0.0,
                        help="GAN discriminator realism weight (default: 0.0)")
    parser.add_argument("--interp", default="linear", choices=("linear", "slerp"),
                        help="latent interpolation method (default: linear)")
    parser.add_argument("--average", action="store_true",
                        help="enable AverageExplorer mode")
    parser.add_argument("--shadow", action="store_true",
                        help="enable ShadowDraw mode")

    parser.add_argument("--python-bin", default="python",
                        help="python executable to place in the generated command (default: python)")
    parser.add_argument("--ui-script", default="iGAN_main.py",
                        help="UI script path to place in the generated command (default: iGAN_main.py)")
    parser.add_argument("--repo-dir", default=".",
                        help="directory used for optional file checks only (default: current directory)")
    parser.add_argument("--device", default="gpu0",
                        help="Theano device value for generated THEANO_FLAGS (default: gpu0)")
    parser.add_argument("--floatx", default="float32",
                        help="Theano floatX value for generated THEANO_FLAGS (default: float32)")
    parser.add_argument("--no-nvcc-fastmath", action="store_true",
                        help="omit nvcc.fastmath=True from generated THEANO_FLAGS")
    parser.add_argument("--extra-theano-flag", action="append", default=[], metavar="KEY=VALUE",
                        help="append an extra THEANO_FLAGS item; may be repeated")
    parser.add_argument("--theano-flags", default=None,
                        help="override the generated THEANO_FLAGS string exactly")
    parser.add_argument("--no-theano-flags", action="store_true",
                        help="do not include THEANO_FLAGS in the generated command")
    parser.add_argument("--check-display", action="store_true",
                        help="report whether DISPLAY is set; does not launch any UI")
    parser.add_argument("--require-display", action="store_true",
                        help="exit nonzero if DISPLAY is not set")
    parser.add_argument("--check-model-file", action="store_true",
                        help="report whether the resolved model file exists under --repo-dir")
    parser.add_argument("--require-model-file", action="store_true",
                        help="exit nonzero if the resolved model file does not exist")
    parser.add_argument("--format", choices=("shell", "json"), default="shell",
                        help="output format (default: shell)")
    return parser


def default_model_file(model_name: str, model_type: str) -> str:
    return f"./models/{model_name}.{model_type}"


def build_theano_flags(args: argparse.Namespace) -> str | None:
    if args.no_theano_flags:
        return None
    if args.theano_flags is not None:
        return args.theano_flags
    flags = [f"device={args.device}", f"floatX={args.floatx}"]
    if not args.no_nvcc_fastmath:
        flags.append("nvcc.fastmath=True")
    flags.extend(args.extra_theano_flag)
    return ",".join(flags)


def build_argv(args: argparse.Namespace, resolved_model_file: str) -> List[str]:
    argv = [
        args.python_bin,
        args.ui_script,
        "--model_name", args.model_name,
        "--model_type", args.model_type,
        "--framework", args.framework,
        "--win_size", str(args.win_size),
        "--batch_size", str(args.batch_size),
        "--n_iters", str(args.n_iters),
        "--top_k", str(args.top_k),
        "--morph_steps", str(args.morph_steps),
        "--d_weight", str(args.d_weight),
        "--interp", args.interp,
    ]
    if args.model_file is not None:
        argv.extend(["--model_file", resolved_model_file])
    if args.average:
        argv.append("--average")
    if args.shadow:
        argv.append("--shadow")
    return argv


def shell_command(env: Dict[str, str], argv: List[str]) -> str:
    prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in sorted(env.items()))
    command = shlex.join(argv)
    if prefix:
        return f"{prefix} {command}"
    return command


def resolve_for_check(repo_dir: str, model_file: str) -> Path:
    path = Path(model_file)
    if path.is_absolute():
        return path
    return Path(repo_dir) / path


def collect_checks(args: argparse.Namespace, resolved_model_file: str) -> Tuple[List[Dict[str, object]], List[str], int]:
    checks: List[Dict[str, object]] = []
    warnings: List[str] = []
    exit_code = 0

    if args.check_display or args.require_display:
        display = os.environ.get("DISPLAY", "")
        ok = bool(display)
        checks.append({"name": "display", "ok": ok, "value": display or None})
        if not ok:
            warnings.append("DISPLAY is not set; PyQt4 launch needs a local display, VNC, Xpra, or X forwarding.")
            if args.require_display:
                exit_code = 2

    if args.check_model_file or args.require_model_file:
        check_path = resolve_for_check(args.repo_dir, resolved_model_file)
        ok = check_path.exists()
        checks.append({"name": "model_file", "ok": ok, "path": str(check_path)})
        if not ok:
            warnings.append(
                "Resolved model file is missing; download or place the pretrained artifact before launching."
            )
            if args.require_model_file:
                exit_code = 3 if exit_code == 0 else exit_code

    if args.shadow and args.model_name != "hed_shoes_64":
        warnings.append(
            "ShadowDraw is documented for hed_shoes_64; other models may launch but provide poor sketch guidance."
        )

    if args.shadow and not args.average:
        warnings.append("ShadowDraw is commonly used with --average for cursor guidance.")

    if args.device == "cpu":
        warnings.append("CPU mode may be useful for diagnostics but is not expected to provide real-time UI updates.")

    if args.framework != "theano" or args.model_type != "dcgan_theano":
        warnings.append(
            "Non-default framework/model_type requires matching model_def and constrained_opt modules in the checkout."
        )

    return checks, warnings, exit_code


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    resolved_model_file = args.model_file or default_model_file(args.model_name, args.model_type)
    env: Dict[str, str] = {}
    theano_flags = build_theano_flags(args)
    if theano_flags is not None:
        env["THEANO_FLAGS"] = theano_flags

    command_argv = build_argv(args, resolved_model_file)
    command = shell_command(env, command_argv)
    checks, warnings, exit_code = collect_checks(args, resolved_model_file)

    payload = {
        "command": command,
        "env": env,
        "argv": command_argv,
        "model_file": resolved_model_file,
        "dry_run": True,
        "checks": checks,
        "warnings": warnings,
        "notes": [
            "This helper does not launch PyQt4 or import iGAN modules.",
            "Run the command only inside a compatible legacy iGAN checkout with model artifacts available.",
        ],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
        if checks:
            print("\nChecks:")
            for check in checks:
                status = "ok" if check.get("ok") else "missing"
                detail = check.get("value") or check.get("path") or ""
                print(f"- {check['name']}: {status}{(' (' + str(detail) + ')') if detail else ''}")
        if warnings:
            print("\nWarnings:", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

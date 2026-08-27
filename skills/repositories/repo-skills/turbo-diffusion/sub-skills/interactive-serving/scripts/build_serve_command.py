#!/usr/bin/env python3
"""Render a TurboDiffusion interactive serving command without executing it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

MODEL_CHOICES = ("Wan2.1-1.3B", "Wan2.1-14B", "Wan2.2-A14B")
ATTENTION_CHOICES = ("sla", "sagesla", "original")
RESOLUTION_ASPECTS = {
    "720": ("1:1", "4:3", "3:4", "16:9", "9:16"),
    "512": ("1:1", "4:3", "3:4", "16:9", "9:16"),
    "480": ("1:1", "4:3", "3:4", "16:9", "9:16"),
    "480p": ("1:1", "4:3", "3:4", "16:9", "9:16"),
    "720p": ("1:1", "4:3", "3:4", "16:9", "9:16"),
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def boundary_float(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed < 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def topk_float(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("must be in (0, 1]")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboDiffusion TUI server command. This helper validates "
            "mode-specific required paths and prints a command; it never launches "
            "models, downloads assets, or starts generation."
        )
    )
    parser.add_argument("--mode", choices=("t2v", "i2v"), required=True)
    parser.add_argument(
        "--launch-method",
        choices=("cli", "module"),
        default="cli",
        help="Use the installed turbodiffusion-serve entry point or python -m turbodiffusion.serve.",
    )
    parser.add_argument("--python", default="python", help="Python executable name for --launch-method module.")
    parser.add_argument(
        "--source-layout-dir",
        default="turbodiffusion",
        help=(
            "Directory to prepend as PYTHONPATH for source-layout imports. "
            "Use --no-source-layout-pythonpath if imaginaire/rcm are already importable."
        ),
    )
    parser.add_argument(
        "--no-source-layout-pythonpath",
        action="store_true",
        help="Do not render a PYTHONPATH prefix.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Render the command even if required model path files do not exist on this machine.",
    )
    parser.add_argument(
        "--output",
        choices=("shell", "argv", "json"),
        default="shell",
        help="Output shell command, one argv token per line, or structured JSON.",
    )

    # Mode-specific model paths.
    parser.add_argument("--dit-path", dest="dit_path", help="T2V DiT checkpoint path; rendered as --dit_path.")
    parser.add_argument(
        "--high-noise-model-path",
        dest="high_noise_model_path",
        help="I2V high-noise checkpoint path; rendered as --high_noise_model_path.",
    )
    parser.add_argument(
        "--low-noise-model-path",
        dest="low_noise_model_path",
        help="I2V low-noise checkpoint path; rendered as --low_noise_model_path.",
    )
    parser.add_argument(
        "--boundary",
        type=boundary_float,
        default=0.9,
        help="I2V high-to-low noise switch boundary; rendered only for i2v.",
    )

    # Model configuration.
    parser.add_argument("--model", choices=MODEL_CHOICES, help="Model architecture; mode default is used if omitted.")
    parser.add_argument("--vae-path", dest="vae_path", help="Optional VAE path; rendered as --vae_path.")
    parser.add_argument(
        "--text-encoder-path",
        dest="text_encoder_path",
        help="Optional text encoder path; rendered as --text_encoder_path.",
    )
    parser.add_argument("--resolution", help="Resolution key; mode default is used if omitted.")
    parser.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio key; rendered as --aspect_ratio.")
    parser.add_argument("--adaptive-resolution", action="store_true", help="I2V adaptive image-aspect resolution.")

    # Acceleration/model construction.
    parser.add_argument("--attention-type", choices=ATTENTION_CHOICES, default="sagesla", help="Rendered as --attention_type.")
    parser.add_argument("--sla-topk", type=topk_float, default=0.1, help="Rendered as --sla_topk.")
    parser.add_argument("--quant-linear", action="store_true", help="Render --quant_linear.")
    parser.add_argument("--default-norm", action="store_true", help="Render --default_norm.")

    # Sampling/runtime initialization.
    parser.add_argument("--ode", action="store_true", help="I2V ODE sampling flag.")
    parser.add_argument("--num-steps", type=int, choices=(1, 2, 3, 4), default=4, help="Rendered as --num_steps.")
    parser.add_argument("--num-samples", type=positive_int, default=1, help="Rendered as --num_samples.")
    parser.add_argument("--num-frames", type=positive_int, default=81, help="Rendered as --num_frames.")
    parser.add_argument("--sigma-max", type=positive_float, help="Rendered as --sigma_max; mode default is used if omitted.")
    parser.add_argument("--seed", type=int, default=0, help="Rendered as --seed.")
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    errors: list[str] = []
    required_files: list[tuple[str, str]] = []

    if args.model is None:
        args.model = "Wan2.1-1.3B" if args.mode == "t2v" else "Wan2.2-A14B"
    if args.resolution is None:
        args.resolution = "480p" if args.mode == "t2v" else "720p"
    if args.sigma_max is None:
        args.sigma_max = 80.0 if args.mode == "t2v" else 200.0

    if args.mode == "t2v":
        if not args.dit_path:
            errors.append("--dit-path is required for --mode t2v")
        else:
            required_files.append(("--dit-path", args.dit_path))
        if args.high_noise_model_path or args.low_noise_model_path:
            errors.append("I2V high/low model paths are not used in --mode t2v")
        if args.adaptive_resolution:
            errors.append("--adaptive-resolution is I2V-only")
        if args.ode:
            errors.append("--ode is I2V-only")
    else:
        if not args.high_noise_model_path:
            errors.append("--high-noise-model-path is required for --mode i2v")
        else:
            required_files.append(("--high-noise-model-path", args.high_noise_model_path))
        if not args.low_noise_model_path:
            errors.append("--low-noise-model-path is required for --mode i2v")
        else:
            required_files.append(("--low-noise-model-path", args.low_noise_model_path))
        if args.dit_path:
            errors.append("--dit-path is not used in --mode i2v")
        if args.high_noise_model_path and args.low_noise_model_path:
            if Path(args.high_noise_model_path).expanduser() == Path(args.low_noise_model_path).expanduser():
                errors.append("I2V high-noise and low-noise model paths must be distinct")

    if args.resolution not in RESOLUTION_ASPECTS:
        errors.append(
            f"invalid --resolution {args.resolution!r}; choose one of {', '.join(RESOLUTION_ASPECTS)}"
        )
    elif args.aspect_ratio not in RESOLUTION_ASPECTS[args.resolution]:
        errors.append(
            f"invalid --aspect-ratio {args.aspect_ratio!r} for resolution {args.resolution!r}; "
            f"choose one of {', '.join(RESOLUTION_ASPECTS[args.resolution])}"
        )

    if not args.allow_missing:
        for label, value in required_files:
            candidate = Path(value).expanduser()
            if not candidate.is_file():
                errors.append(f"{label} does not point to an existing file: {value}")

    if errors:
        parser.error("\n  " + "\n  ".join(errors))


def append_option(argv: list[str], name: str, value: Any) -> None:
    argv.extend((f"--{name}", str(value)))


def append_flag(argv: list[str], name: str, enabled: bool) -> None:
    if enabled:
        argv.append(f"--{name}")


def build_server_argv(args: argparse.Namespace) -> list[str]:
    argv = ["turbodiffusion-serve"] if args.launch_method == "cli" else [args.python, "-m", "turbodiffusion.serve"]

    append_option(argv, "mode", args.mode)
    if args.mode == "t2v":
        append_option(argv, "dit_path", args.dit_path)
    else:
        append_option(argv, "high_noise_model_path", args.high_noise_model_path)
        append_option(argv, "low_noise_model_path", args.low_noise_model_path)
        append_option(argv, "boundary", args.boundary)
        append_flag(argv, "adaptive_resolution", args.adaptive_resolution)
        append_flag(argv, "ode", args.ode)

    append_option(argv, "model", args.model)
    if args.vae_path:
        append_option(argv, "vae_path", args.vae_path)
    if args.text_encoder_path:
        append_option(argv, "text_encoder_path", args.text_encoder_path)
    append_option(argv, "resolution", args.resolution)
    append_option(argv, "aspect_ratio", args.aspect_ratio)
    append_option(argv, "attention_type", args.attention_type)
    append_option(argv, "sla_topk", args.sla_topk)
    append_flag(argv, "quant_linear", args.quant_linear)
    append_flag(argv, "default_norm", args.default_norm)
    append_option(argv, "num_steps", args.num_steps)
    append_option(argv, "num_samples", args.num_samples)
    append_option(argv, "num_frames", args.num_frames)
    append_option(argv, "sigma_max", args.sigma_max)
    append_option(argv, "seed", args.seed)
    return argv


def shell_command(env: dict[str, str], argv: list[str]) -> str:
    prefix = [f"{key}={shlex.quote(value)}" for key, value in env.items()]
    return " ".join(prefix + [shlex.quote(token) for token in argv])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)

    env = {}
    if not args.no_source_layout_pythonpath:
        env["PYTHONPATH"] = args.source_layout_dir

    server_argv = build_server_argv(args)
    rendered_shell = shell_command(env, server_argv)

    if args.output == "shell":
        print(rendered_shell)
    elif args.output == "argv":
        for token in server_argv:
            print(token)
    else:
        print(json.dumps({"env": env, "argv": server_argv, "shell": rendered_shell}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

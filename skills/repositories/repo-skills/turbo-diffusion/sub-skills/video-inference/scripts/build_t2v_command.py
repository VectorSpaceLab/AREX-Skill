#!/usr/bin/env python3
"""Render a TurboDiffusion Wan2.1 T2V command without running a model."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".gif", ".webm"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def topk_ratio(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("must be in the interval (0, 1]")
    return parsed


def nonempty(name: str, value: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{name} must be non-empty")
    if re.search(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(value)):
        raise ValueError(f"{name} must be a local path, not a URL")
    return str(value)


def prompt_from_args(args: argparse.Namespace) -> str:
    if bool(args.prompt) == bool(args.prompt_file):
        raise ValueError("provide exactly one of --prompt or --prompt-file")
    if args.prompt_file:
        prompt_path = Path(nonempty("--prompt-file", args.prompt_file))
        if args.check_files and not prompt_path.is_file():
            raise ValueError(f"prompt file does not exist: {prompt_path}")
        text = prompt_path.read_text(encoding="utf-8").strip()
    else:
        text = str(args.prompt).strip()
    if not text:
        raise ValueError("prompt must be non-empty")
    return text


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def validate(args: argparse.Namespace) -> str:
    args.dit_path = nonempty("--dit-path", args.dit_path)
    args.vae_path = nonempty("--vae-path", args.vae_path)
    args.text_encoder_path = nonempty("--text-encoder-path", args.text_encoder_path)
    args.save_path = nonempty("--save-path", args.save_path)
    args.script = nonempty("--script", args.script)
    args.python = nonempty("--python", args.python)

    if not re.fullmatch(r"\d+:\d+", args.aspect_ratio):
        raise ValueError("--aspect-ratio must look like W:H, for example 16:9")

    suffix = Path(args.save_path).suffix.lower()
    if suffix not in VIDEO_SUFFIXES:
        raise ValueError(f"--save-path must end with one of {sorted(VIDEO_SUFFIXES)}")

    if args.check_files:
        for label, raw_path in [
            ("DiT checkpoint", args.dit_path),
            ("VAE checkpoint", args.vae_path),
            ("text encoder checkpoint", args.text_encoder_path),
        ]:
            if not Path(raw_path).is_file():
                raise ValueError(f"{label} does not exist: {raw_path}")

    prompt = prompt_from_args(args)
    if len(prompt) < 80:
        warn("TurboDiffusion README notes current models are trained on long English prompts; consider expanding this prompt")
    if sum(ord(ch) < 128 for ch in prompt) / max(len(prompt), 1) < 0.85:
        warn("prompt contains many non-ASCII characters; README guidance favors long English prompts")

    basename = Path(args.dit_path).name.lower()
    looks_quantized = "quant" in basename
    if looks_quantized and not args.quant_linear and not args.allow_flag_mismatch:
        raise ValueError("checkpoint name looks quantized but --quant-linear was not provided")
    if args.quant_linear and not looks_quantized and not args.allow_flag_mismatch:
        warn("--quant-linear is set but checkpoint basename does not contain 'quant'; verify checkpoint format")

    if not args.allow_flag_mismatch:
        if args.model == "Wan2.1-1.3B" and "14b" in basename:
            raise ValueError("--model Wan2.1-1.3B does not match a checkpoint basename containing 14B")
        if args.model == "Wan2.1-14B" and "1.3b" in basename:
            raise ValueError("--model Wan2.1-14B does not match a checkpoint basename containing 1.3B")

    if "480p" in basename and args.resolution == "720p":
        warn("checkpoint basename contains 480P but --resolution is 720p; README lists best resolution separately from supported resolutions")
    if "720p" in basename and args.resolution == "480p":
        warn("checkpoint basename contains 720P but --resolution is 480p; README lists best resolution separately from supported resolutions")

    if args.attention_type == "sagesla":
        warn("attention_type=sagesla needs optional SpargeAttn/SageSLA support in the runtime environment")

    return prompt


def segment(flag: str, value: object | None = None) -> str:
    if value is None:
        return flag
    return f"{flag} {shlex.quote(str(value))}"


def render_command(args: argparse.Namespace, prompt: str) -> str:
    argv_head = [shlex.quote(args.python), shlex.quote(args.script)]
    env_prefix = ""
    if not args.no_pythonpath:
        pythonpath = nonempty("--pythonpath", args.pythonpath)
        env_prefix = f"PYTHONPATH={shlex.quote(pythonpath)} "

    pieces = [
        segment("--model", args.model),
        segment("--dit_path", args.dit_path),
        segment("--vae_path", args.vae_path),
        segment("--text_encoder_path", args.text_encoder_path),
        segment("--prompt", prompt),
        segment("--resolution", args.resolution),
        segment("--aspect_ratio", args.aspect_ratio),
        segment("--num_samples", args.num_samples),
        segment("--num_steps", args.num_steps),
        segment("--sigma_max", args.sigma_max),
        segment("--num_frames", args.num_frames),
        segment("--seed", args.seed),
        segment("--save_path", args.save_path),
        segment("--attention_type", args.attention_type),
        segment("--sla_topk", args.sla_topk),
    ]
    if args.quant_linear:
        pieces.append(segment("--quant_linear"))
    if args.default_norm:
        pieces.append(segment("--default_norm"))

    head = env_prefix + " ".join(argv_head)
    if args.one_line:
        return head + " " + " ".join(pieces)
    return head + " \\\n  " + " \\\n  ".join(pieces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboDiffusion Wan2.1 text-to-video command. "
            "This helper performs local string/path validation only and never runs inference."
        )
    )
    parser.add_argument("--python", default="python", help="Python executable name for the rendered command")
    parser.add_argument("--script", default="turbodiffusion/inference/wan2.1_t2v_infer.py", help="Inference script path for the rendered command")
    parser.add_argument("--pythonpath", default="turbodiffusion", help="Source-layout PYTHONPATH value to include")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prefix the rendered command with PYTHONPATH")
    parser.add_argument("--one-line", action="store_true", help="Render a one-line command instead of a multiline command")
    parser.add_argument("--check-files", action="store_true", help="Require referenced local asset files to exist before rendering")
    parser.add_argument("--allow-flag-mismatch", action="store_true", help="Bypass quantization/model-name filename heuristics")

    parser.add_argument("--dit-path", required=True, help="Local T2V DiT checkpoint path")
    parser.add_argument("--vae-path", required=True, help="Local Wan VAE checkpoint path")
    parser.add_argument("--text-encoder-path", required=True, help="Local umT5 text encoder checkpoint path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", help="Long English prompt to pass to --prompt")
    group.add_argument("--prompt-file", help="UTF-8 text file containing the prompt")

    parser.add_argument("--model", choices=["Wan2.1-1.3B", "Wan2.1-14B"], default="Wan2.1-1.3B")
    parser.add_argument("--num-samples", type=positive_int, default=1)
    parser.add_argument("--num-steps", type=int, choices=[1, 2, 3, 4], default=4)
    parser.add_argument("--sigma-max", type=positive_float, default=80)
    parser.add_argument("--num-frames", type=positive_int, default=81)
    parser.add_argument("--resolution", choices=["480p", "720p"], default="480p")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--save-path", default="output/generated_video.mp4")
    parser.add_argument("--attention-type", choices=["sla", "sagesla", "original"], default="sagesla")
    parser.add_argument("--sla-topk", type=topk_ratio, default=0.1)
    parser.add_argument("--quant-linear", action="store_true", help="Add --quant_linear for quantized checkpoints")
    parser.add_argument("--default-norm", action="store_true", help="Add --default_norm to keep original norm layers")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        prompt = validate(args)
        print(render_command(args, prompt))
    except Exception as exc:  # noqa: BLE001 - argparse-style CLI helper
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

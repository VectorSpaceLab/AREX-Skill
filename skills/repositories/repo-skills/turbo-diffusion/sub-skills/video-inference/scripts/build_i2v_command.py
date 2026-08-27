#!/usr/bin/env python3
"""Render a TurboDiffusion Wan2.2 I2V command without running a model."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".gif", ".webm"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


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


def boundary_value(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed < 1:
        raise argparse.ArgumentTypeError("must be in the interval (0, 1)")
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


def contains_word(path: str, word: str) -> bool:
    return bool(re.search(rf"(?:^|[^a-z0-9]){re.escape(word)}(?:[^a-z0-9]|$)", Path(path).name.lower()))


def validate(args: argparse.Namespace) -> str:
    args.high_noise_model_path = nonempty("--high-noise-model-path", args.high_noise_model_path)
    args.low_noise_model_path = nonempty("--low-noise-model-path", args.low_noise_model_path)
    args.vae_path = nonempty("--vae-path", args.vae_path)
    args.text_encoder_path = nonempty("--text-encoder-path", args.text_encoder_path)
    args.image_path = nonempty("--image-path", args.image_path)
    args.save_path = nonempty("--save-path", args.save_path)
    args.script = nonempty("--script", args.script)
    args.python = nonempty("--python", args.python)

    if not re.fullmatch(r"\d+:\d+", args.aspect_ratio):
        raise ValueError("--aspect-ratio must look like W:H, for example 16:9")

    image_suffix = Path(args.image_path).suffix.lower()
    if image_suffix and image_suffix not in IMAGE_SUFFIXES:
        warn(f"image suffix {image_suffix!r} is unusual; expected one of {sorted(IMAGE_SUFFIXES)}")
    if not image_suffix:
        warn("image path has no suffix; PIL may still open it, but explicit .jpg/.png/.webp is safer")

    video_suffix = Path(args.save_path).suffix.lower()
    if video_suffix not in VIDEO_SUFFIXES:
        raise ValueError(f"--save-path must end with one of {sorted(VIDEO_SUFFIXES)}")

    if args.check_files:
        for label, raw_path in [
            ("high-noise checkpoint", args.high_noise_model_path),
            ("low-noise checkpoint", args.low_noise_model_path),
            ("VAE checkpoint", args.vae_path),
            ("text encoder checkpoint", args.text_encoder_path),
            ("input image", args.image_path),
        ]:
            if not Path(raw_path).is_file():
                raise ValueError(f"{label} does not exist: {raw_path}")

    prompt = prompt_from_args(args)
    if len(prompt) < 80:
        warn("TurboDiffusion README notes current models are trained on long English prompts; consider expanding this prompt")
    if sum(ord(ch) < 128 for ch in prompt) / max(len(prompt), 1) < 0.85:
        warn("prompt contains many non-ASCII characters; README guidance favors long English prompts")

    high_name = Path(args.high_noise_model_path).name.lower()
    low_name = Path(args.low_noise_model_path).name.lower()
    high_quant = "quant" in high_name
    low_quant = "quant" in low_name

    if not args.allow_flag_mismatch:
        if contains_word(args.high_noise_model_path, "low"):
            raise ValueError("--high-noise-model-path basename looks like a low-noise checkpoint")
        if contains_word(args.low_noise_model_path, "high"):
            raise ValueError("--low-noise-model-path basename looks like a high-noise checkpoint")
        if high_quant != low_quant:
            raise ValueError("high/low checkpoint basenames indicate mixed quantized and unquantized formats")
        if (high_quant or low_quant) and not args.quant_linear:
            raise ValueError("I2V checkpoint names look quantized but --quant-linear was not provided")

    if args.quant_linear and not (high_quant or low_quant) and not args.allow_flag_mismatch:
        warn("--quant-linear is set but neither checkpoint basename contains 'quant'; verify checkpoint format")

    for label, name in [("high", high_name), ("low", low_name)]:
        if "480p" in name and args.resolution == "720p":
            warn(f"{label}-noise checkpoint basename contains 480P but --resolution is 720p")
        if "720p" in name and args.resolution == "480p":
            warn(f"{label}-noise checkpoint basename contains 720P but --resolution is 480p")

    if args.adaptive_resolution:
        warn("adaptive resolution uses the input image aspect ratio with the selected resolution/aspect-ratio area budget")

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
        segment("--high_noise_model_path", args.high_noise_model_path),
        segment("--low_noise_model_path", args.low_noise_model_path),
        segment("--vae_path", args.vae_path),
        segment("--text_encoder_path", args.text_encoder_path),
        segment("--image_path", args.image_path),
        segment("--prompt", prompt),
        segment("--resolution", args.resolution),
        segment("--aspect_ratio", args.aspect_ratio),
        segment("--num_samples", args.num_samples),
        segment("--num_steps", args.num_steps),
        segment("--sigma_max", args.sigma_max),
        segment("--boundary", args.boundary),
        segment("--num_frames", args.num_frames),
        segment("--seed", args.seed),
        segment("--save_path", args.save_path),
        segment("--attention_type", args.attention_type),
        segment("--sla_topk", args.sla_topk),
    ]
    if args.adaptive_resolution:
        pieces.append(segment("--adaptive_resolution"))
    if args.ode:
        pieces.append(segment("--ode"))
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
            "Render a TurboDiffusion Wan2.2 image-to-video command. "
            "This helper performs local string/path validation only and never runs inference."
        )
    )
    parser.add_argument("--python", default="python", help="Python executable name for the rendered command")
    parser.add_argument("--script", default="turbodiffusion/inference/wan2.2_i2v_infer.py", help="Inference script path for the rendered command")
    parser.add_argument("--pythonpath", default="turbodiffusion", help="Source-layout PYTHONPATH value to include")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prefix the rendered command with PYTHONPATH")
    parser.add_argument("--one-line", action="store_true", help="Render a one-line command instead of a multiline command")
    parser.add_argument("--check-files", action="store_true", help="Require referenced local asset/image files to exist before rendering")
    parser.add_argument("--allow-flag-mismatch", action="store_true", help="Bypass quantization and high/low filename heuristics")

    parser.add_argument("--high-noise-model-path", required=True, help="Local I2V high-noise DiT checkpoint path")
    parser.add_argument("--low-noise-model-path", required=True, help="Local I2V low-noise DiT checkpoint path")
    parser.add_argument("--vae-path", required=True, help="Local Wan VAE checkpoint path")
    parser.add_argument("--text-encoder-path", required=True, help="Local umT5 text encoder checkpoint path")
    parser.add_argument("--image-path", required=True, help="Local input image path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", help="Long English prompt to pass to --prompt")
    group.add_argument("--prompt-file", help="UTF-8 text file containing the prompt")

    parser.add_argument("--model", choices=["Wan2.2-A14B"], default="Wan2.2-A14B")
    parser.add_argument("--num-samples", type=positive_int, default=1)
    parser.add_argument("--num-steps", type=int, choices=[1, 2, 3, 4], default=4)
    parser.add_argument("--sigma-max", type=positive_float, default=200)
    parser.add_argument("--boundary", type=boundary_value, default=0.9)
    parser.add_argument("--num-frames", type=positive_int, default=81)
    parser.add_argument("--resolution", choices=["480p", "720p"], default="720p")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--adaptive-resolution", action="store_true", help="Add --adaptive_resolution")
    parser.add_argument("--ode", action="store_true", help="Add --ode")
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

#!/usr/bin/env python3
"""Build a safe LTX-2.5 split DistilledPipeline command.

The script validates local path existence by default, checks basic frame and
resolution constraints, and prints a shell-quoted command. It does not import
ltx_pipelines, instantiate models, download files, or run generation.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Iterable

DEFAULT_RELATIVE = {
    "transformer_path": "diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors",
    "text_encoder_path": "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
    "video_vae_path": "vae/ltx-2.5-video-vae-bf16.safetensors",
    "audio_vae_path": "vae/ltx-2.5-audio-vae-bf16.safetensors",
    "spatial_upsampler_path": "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors",
}

HDR_CHOICES = ("SRGB_LINEAR", "ACESCG", "ACESCCT")
OFFLOAD_CHOICES = ("none", "cpu", "disk")
QUANTIZATION_CHOICES = ("fp8-cast", "fp8-scaled-mm", "nvfp4-cast", "nvfp4-prequant")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def parse_lora(value: str) -> tuple[str, str | None]:
    """Parse PATH or PATH:STRENGTH without breaking Windows drive-like paths.

    For POSIX runtime use the final ':' as the strength separator only when the
    suffix parses as a float.
    """
    path, sep, maybe_strength = value.rpartition(":")
    if sep:
        try:
            float(maybe_strength)
        except ValueError:
            return value, None
        return path, maybe_strength
    return value, None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell command for LTX-2.5 split DistilledPipeline. "
            "The command is not executed. Required model paths are validated unless --no-validate-paths is used."
        )
    )
    assets = parser.add_argument_group("model assets")
    assets.add_argument(
        "--model-root",
        help=(
            "Directory containing the public LTX-2.5 component layout. Missing explicit asset paths are derived from it."
        ),
    )
    assets.add_argument("--transformer-path", help="Distilled transformer safetensors.")
    assets.add_argument("--text-encoder-path", help="LTX Gemma/text-projection single-file safetensors.")
    assets.add_argument("--video-vae-path", help="Video VAE safetensors.")
    assets.add_argument("--audio-vae-path", help="Audio VAE safetensors.")
    assets.add_argument("--spatial-upsampler-path", help="Latent spatial upsampler safetensors.")
    assets.add_argument("--duration-head-path", help="Optional duration-head safetensors for auto-duration.")
    assets.add_argument(
        "--lora",
        action="append",
        default=[],
        metavar="PATH[:STRENGTH]",
        help="Optional LoRA for DistilledPipeline; repeatable. Strength defaults to parser default when omitted.",
    )

    run = parser.add_argument_group("generation arguments to include in printed command")
    run.add_argument("--prompt", required=True, help="Prompt text to put in the command.")
    run.add_argument("--output-path", required=True, help="Output MP4 path to put in the command.")
    run.add_argument("--image", help="Optional image conditioning still path.")
    run.add_argument("--image-frame", type=nonnegative_int, default=0, help="Frame index for --image (default: 0).")
    run.add_argument("--image-strength", type=float, default=1.0, help="Strength for --image (default: 1.0).")
    run.add_argument("--image-crf", type=nonnegative_int, help="Optional CRF appended to --image.")
    run.add_argument("--height", type=positive_int, default=1024, help="Output height, multiple of 64 (default: 1024).")
    run.add_argument("--width", type=positive_int, default=1536, help="Output width, multiple of 64 (default: 1536).")
    run.add_argument("--num-frames", type=positive_int, default=121, help="Frame count, must be 8*k+1 (default: 121).")
    run.add_argument("--frame-rate", type=positive_float, default=24.0, help="Frame rate (default: 24).")
    run.add_argument("--seed", type=int, default=42, help="Seed (default: 42).")
    run.add_argument("--offload", choices=OFFLOAD_CHOICES, help="Optional offload flag to include.")
    run.add_argument("--quantization", choices=QUANTIZATION_CHOICES, help="Optional quantization flag to include.")
    run.add_argument("--compile", nargs="*", metavar="KEY=VALUE", help="Optional torch.compile flag and overrides.")
    run.add_argument("--diffvae-optimization", help="Optional DiffVAE optimization mode to include.")
    run.add_argument("--num-generated-keyframes", type=nonnegative_int, help="Optional generated keyframe count.")
    run.add_argument("--hdr", choices=HDR_CHOICES, help="HDR color space; required if --image is an .exr still.")
    run.add_argument("--enhance-prompt", action="store_true", help="Include --enhance-prompt.")
    run.add_argument("--prompt-enhancer-gemma-root", help="Optional prompt enhancer root path to include.")

    output = parser.add_argument_group("builder behavior")
    output.add_argument("--python", default="python", help="Python executable token for the printed command (default: python).")
    output.add_argument("--uv-run", action="store_true", help="Print command prefixed with 'uv run python' instead of --python.")
    output.add_argument("--no-validate-paths", action="store_true", help="Do not require local asset/input paths to exist.")
    output.add_argument("--json", action="store_true", help="Emit JSON with argv array and shell command.")
    return parser


def derived_path(args: argparse.Namespace, key: str) -> str | None:
    explicit = getattr(args, key)
    if explicit:
        return explicit
    if args.model_root and key in DEFAULT_RELATIVE:
        return str(Path(args.model_root) / DEFAULT_RELATIVE[key])
    return None


def validate_exists(label: str, path: str) -> None:
    if not Path(path).expanduser().exists():
        raise SystemExit(f"{label} does not exist: {path}")


def validate_args(args: argparse.Namespace, paths: dict[str, str]) -> None:
    if args.height % 64 != 0 or args.width % 64 != 0:
        raise SystemExit(f"DistilledPipeline is two-stage; height and width must be multiples of 64, got {args.height}x{args.width}")
    if (args.num_frames - 1) % 8 != 0:
        raise SystemExit(f"--num-frames must satisfy 8*k+1, got {args.num_frames}")
    if not args.prompt.strip():
        raise SystemExit("--prompt must not be empty")
    if args.image and args.image.lower().endswith(".exr") and not args.hdr:
        raise SystemExit("EXR --image requires --hdr {SRGB_LINEAR,ACESCG,ACESCCT}")
    if args.compile is not None:
        for item in args.compile:
            if "=" not in item:
                raise SystemExit(f"--compile overrides must be KEY=VALUE, got {item!r}")
    if not args.no_validate_paths:
        for key, path in paths.items():
            validate_exists("--" + key.replace("_", "-"), path)
        if args.duration_head_path:
            validate_exists("--duration-head-path", args.duration_head_path)
        if args.image:
            validate_exists("--image", args.image)
        if args.prompt_enhancer_gemma_root:
            validate_exists("--prompt-enhancer-gemma-root", args.prompt_enhancer_gemma_root)
        for raw_lora in args.lora:
            lora_path, _ = parse_lora(raw_lora)
            validate_exists("--lora", lora_path)


def extend_flag(argv: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def append_loras(argv: list[str], loras: Iterable[str]) -> None:
    for raw in loras:
        path, strength = parse_lora(raw)
        argv.extend(["--lora", path])
        if strength is not None:
            argv.append(strength)


def build_command(args: argparse.Namespace, paths: dict[str, str]) -> list[str]:
    argv: list[str]
    if args.uv_run:
        argv = ["uv", "run", "python", "-m", "ltx_pipelines.distilled"]
    else:
        argv = [args.python, "-m", "ltx_pipelines.distilled"]

    for key, flag in [
        ("transformer_path", "--transformer-path"),
        ("text_encoder_path", "--text-encoder-path"),
        ("video_vae_path", "--video-vae-path"),
        ("audio_vae_path", "--audio-vae-path"),
        ("spatial_upsampler_path", "--spatial-upsampler-path"),
    ]:
        argv.extend([flag, paths[key]])
    extend_flag(argv, "--duration-head-path", args.duration_head_path)
    append_loras(argv, args.lora)

    argv.extend(["--prompt", args.prompt, "--output-path", args.output_path])
    if args.image:
        argv.extend(["--image", args.image, str(args.image_frame), str(args.image_strength)])
        if args.image_crf is not None:
            argv.append(str(args.image_crf))
    argv.extend(
        [
            "--num-frames",
            str(args.num_frames),
            "--height",
            str(args.height),
            "--width",
            str(args.width),
            "--frame-rate",
            str(args.frame_rate),
            "--seed",
            str(args.seed),
        ]
    )
    extend_flag(argv, "--offload", args.offload)
    extend_flag(argv, "--quantization", args.quantization)
    if args.compile is not None:
        argv.append("--compile")
        argv.extend(args.compile)
    extend_flag(argv, "--diffvae-optimization", args.diffvae_optimization)
    extend_flag(argv, "--num-generated-keyframes", args.num_generated_keyframes)
    extend_flag(argv, "--hdr", args.hdr)
    if args.enhance_prompt:
        argv.append("--enhance-prompt")
    extend_flag(argv, "--prompt-enhancer-gemma-root", args.prompt_enhancer_gemma_root)
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    required = ["transformer_path", "text_encoder_path", "video_vae_path", "audio_vae_path", "spatial_upsampler_path"]
    paths = {key: derived_path(args, key) for key in required}
    missing = ["--" + key.replace("_", "-") for key, value in paths.items() if not value]
    if missing:
        parser.error("missing required asset paths (or --model-root): " + ", ".join(missing))
    resolved_paths = {key: str(value) for key, value in paths.items() if value is not None}

    validate_args(args, resolved_paths)
    command = build_command(args, resolved_paths)
    shell = shlex.join(command)
    if args.json:
        print(json.dumps({"argv": command, "command": shell}, indent=2))
    else:
        print(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

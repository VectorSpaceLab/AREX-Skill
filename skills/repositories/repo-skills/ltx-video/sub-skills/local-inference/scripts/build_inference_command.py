#!/usr/bin/env python3
"""Build a validated LTX-Video inference command without running inference.

The script performs static validation of InferenceConfig-style arguments,
optionally inspects a readable pipeline YAML, prints warnings to stderr, and
prints one shell-safe command to stdout. It never imports ltx_video, loads model
weights, opens media, runs generation, or downloads anything.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
REMOTEISH_PATTERN = re.compile(r"^[\w.-]+/[\w./-]+$")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def padded_dimensions(height: int, width: int, num_frames: int) -> tuple[int, int, int]:
    height_padded = ((height - 1) // 32 + 1) * 32
    width_padded = ((width - 1) // 32 + 1) * 32
    num_frames_padded = ((num_frames - 2) // 8 + 1) * 8 + 1
    return height_padded, width_padded, num_frames_padded


def is_video_path(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def resolve_config_path(pipeline_config: str, repo_root: str | None) -> Path | None:
    raw = Path(os.path.expanduser(pipeline_config))
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(Path.cwd() / raw)
        if repo_root:
            root = Path(os.path.expanduser(repo_root))
            candidates.append(root / raw)
            candidates.append(root / "ltx_video" / raw)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _strip_scalar(raw_value: str) -> str:
    value = raw_value.split("#", 1)[0].strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value


def simple_top_level_yaml(path: Path) -> dict[str, Any]:
    """Parse simple top-level key: scalar lines when PyYAML is unavailable."""
    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = _strip_scalar(value)
        if value == "":
            continue
        if value.lower() in {"true", "false"}:
            result[key] = value.lower() == "true"
            continue
        try:
            result[key] = int(value)
            continue
        except ValueError:
            pass
        try:
            result[key] = float(value)
            continue
        except ValueError:
            pass
        result[key] = value
    return result


def load_config_summary(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        import yaml  # type: ignore
    except Exception:
        return simple_top_level_yaml(path), "PyYAML unavailable; used simple top-level YAML parsing"

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - depends on user YAML
        return {}, f"could not parse YAML: {exc}"
    if not isinstance(loaded, dict):
        return {}, "YAML did not parse to a mapping"
    return loaded, None


def field_as_str(config: dict[str, Any], key: str) -> str | None:
    value = config.get(key)
    if value is None:
        return None
    return str(value)


def field_as_int(config: dict[str, Any], key: str) -> int | None:
    value = config.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def local_file_exists(reference: str | None, config_path: Path) -> bool:
    del config_path  # infer() checks checkpoint/upscaler paths as provided from the process cwd.
    if not reference:
        return False
    path = Path(os.path.expanduser(reference))
    if path.is_absolute():
        return path.is_file()
    return path.is_file()


def describe_model_reference(reference: str | None, config_path: Path) -> str:
    if not reference:
        return "missing"
    if local_file_exists(reference, config_path):
        return "local"
    if REMOTEISH_PATTERN.match(reference) or not Path(reference).is_absolute():
        return "non-local"
    return "missing-local-path"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and validate a shell-safe LTX-Video inference command without running inference.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/build_inference_command.py \\\n"
            "    --prompt 'A fox crosses a snowy road at sunrise' \\\n"
            "    --pipeline-config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \\\n"
            "    --output-path outputs/fox --height 704 --width 1216 --num-frames 121\n\n"
            "  python scripts/build_inference_command.py \\\n"
            "    --prompt 'A dancer moves through blue light' \\\n"
            "    --pipeline-config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \\\n"
            "    --output-path outputs/multi \\\n"
            "    --conditioning-media-paths first.png move.mp4 \\\n"
            "    --conditioning-start-frames 0 32 \\\n"
            "    --conditioning-strengths 1.0 0.7\n\n"
            "--repo-root is used only to find a config for optional inspection. "
            "The printed command remains a python inference.py command."
        ),
    )
    parser.add_argument("--prompt", required=True, help="Generation prompt; required by InferenceConfig.")
    parser.add_argument(
        "--pipeline-config",
        "--pipeline_config",
        "--config",
        dest="pipeline_config",
        required=True,
        help="Pipeline YAML path to pass to the inference wrapper.",
    )
    parser.add_argument(
        "--output-path",
        "--output_path",
        dest="output_path",
        required=True,
        help="Output directory to pass as --output_path; infer creates files inside it.",
    )
    parser.add_argument("--height", type=positive_int, default=704, help="Requested output height. Default: 704.")
    parser.add_argument("--width", type=positive_int, default=1216, help="Requested output width. Default: 1216.")
    parser.add_argument(
        "--num-frames",
        "--num_frames",
        dest="num_frames",
        type=positive_int,
        default=121,
        help="Requested frame count. Default: 121.",
    )
    parser.add_argument(
        "--frame-rate",
        "--frame_rate",
        dest="frame_rate",
        type=positive_int,
        default=30,
        help="Output video frame rate. Default: 30.",
    )
    parser.add_argument("--seed", type=int, default=171198, help="Random seed. Default: 171198.")
    parser.add_argument(
        "--negative-prompt",
        "--negative_prompt",
        dest="negative_prompt",
        help="Optional negative prompt. Omit to use the InferenceConfig default.",
    )
    parser.add_argument(
        "--input-media-path",
        "--input_media_path",
        dest="input_media_path",
        help="Image or video path for video-to-video/media modification.",
    )
    parser.add_argument(
        "--image-cond-noise-scale",
        "--image_cond_noise_scale",
        dest="image_cond_noise_scale",
        type=float,
        default=0.15,
        help="Image/conditioning noise scale. Default: 0.15.",
    )
    parser.add_argument(
        "--conditioning-media-paths",
        "--conditioning_media_paths",
        dest="conditioning_media_paths",
        nargs="+",
        help="One or more image/video conditioning paths.",
    )
    parser.add_argument(
        "--conditioning-start-frames",
        "--conditioning_start_frames",
        dest="conditioning_start_frames",
        nargs="+",
        type=int,
        help="One target frame per conditioning path.",
    )
    parser.add_argument(
        "--conditioning-strengths",
        "--conditioning_strengths",
        dest="conditioning_strengths",
        nargs="+",
        type=float,
        help="Optional one strength per conditioning path; defaults to 1.0 each when omitted.",
    )
    parser.add_argument(
        "--offload-to-cpu",
        "--offload_to_cpu",
        dest="offload_to_cpu",
        action="store_true",
        help="Include --offload_to_cpu in the generated command.",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional repository root used only to locate a config file for static warnings.",
    )
    return parser


def validate(args: argparse.Namespace) -> tuple[list[str], list[str], list[float] | None]:
    errors: list[str] = []
    warnings: list[str] = []
    effective_strengths: list[float] | None = None

    height_padded, width_padded, frames_padded = padded_dimensions(
        args.height, args.width, args.num_frames
    )
    if (height_padded, width_padded, frames_padded) != (
        args.height,
        args.width,
        args.num_frames,
    ):
        warnings.append(
            "requested shape will be padded for generation to "
            f"{height_padded}x{width_padded}x{frames_padded} and cropped back to "
            f"{args.height}x{args.width}x{args.num_frames}"
        )

    output_suffix = Path(args.output_path).suffix.lower()
    if output_suffix in {".mp4", ".mov", ".mkv", ".avi", ".png", ".jpg", ".jpeg"}:
        warnings.append(
            "output_path is treated as a directory by infer(); a media-looking suffix "
            f"({output_suffix}) will become a directory name, not the final file name"
        )

    paths = args.conditioning_media_paths
    starts = args.conditioning_start_frames
    strengths = args.conditioning_strengths

    if paths:
        if not starts:
            errors.append("conditioning_media_paths requires conditioning_start_frames")
        if starts and len(paths) != len(starts):
            errors.append("conditioning_media_paths and conditioning_start_frames must have the same length")
        if strengths is not None and len(paths) != len(strengths):
            errors.append("conditioning_media_paths and conditioning_strengths must have the same length")
        effective_strengths = strengths if strengths is not None else [1.0] * len(paths)
        for idx, strength in enumerate(effective_strengths):
            if strength < 0 or strength > 1:
                errors.append(f"conditioning strength at index {idx} must be between 0 and 1")
        if starts:
            for idx, start in enumerate(starts):
                if start < 0 or start >= args.num_frames:
                    errors.append(
                        f"conditioning start frame at index {idx} must be between 0 and {args.num_frames - 1}"
                    )
            for idx, (path, start) in enumerate(zip(paths, starts)):
                if is_video_path(path):
                    if start != 0 and start % 8 != 0:
                        errors.append(
                            "non-first video conditioning sequence at index "
                            f"{idx} starts at frame {start}; use a multiple of 8"
                        )
                    warnings.append(
                        "video conditioning item at index "
                        f"{idx} should have an effective frame count of N*8+1 and fit within num_frames"
                    )
    else:
        if starts:
            errors.append("conditioning_start_frames was provided without conditioning_media_paths")
        if strengths:
            errors.append("conditioning_strengths was provided without conditioning_media_paths")

    config_path = resolve_config_path(args.pipeline_config, args.repo_root)
    if config_path is None:
        warnings.append(
            "could not inspect pipeline config; pass a readable path or --repo-root for network/FP8/multi-scale warnings"
        )
        return errors, warnings, effective_strengths

    config, parse_warning = load_config_summary(config_path)
    if parse_warning:
        warnings.append(f"config inspection note for {args.pipeline_config}: {parse_warning}")
    if not config:
        return errors, warnings, effective_strengths

    pipeline_type = (field_as_str(config, "pipeline_type") or "base").lower()
    precision = (field_as_str(config, "precision") or "").lower()
    checkpoint_path = field_as_str(config, "checkpoint_path")
    upscaler_path = field_as_str(config, "spatial_upscaler_model_path")
    text_encoder = field_as_str(config, "text_encoder_model_name_or_path")

    if pipeline_type == "multi-scale":
        if not upscaler_path:
            errors.append("multi-scale config is missing spatial_upscaler_model_path")
        else:
            warnings.append("multi-scale config detected; spatial upscaler model must be available")
    elif pipeline_type not in {"base", ""}:
        warnings.append(f"unrecognized pipeline_type {pipeline_type!r}; verify config handling before running")

    if checkpoint_path and describe_model_reference(checkpoint_path, config_path) != "local":
        warnings.append(
            "checkpoint_path is not a readable local file as provided from the current working directory; "
            "infer() may download it from Hugging Face repo Lightricks/LTX-Video"
        )
    if upscaler_path and describe_model_reference(upscaler_path, config_path) != "local":
        warnings.append(
            "spatial_upscaler_model_path is not a readable local file as provided from the current working directory; "
            "multi-scale infer() may download it from Hugging Face repo Lightricks/LTX-Video"
        )
    if text_encoder and describe_model_reference(text_encoder, config_path) != "local":
        warnings.append(
            "text_encoder_model_name_or_path is not a readable local path; Transformers may use cache/network"
        )

    if precision == "float8_e4m3fn":
        warnings.append("FP8 precision detected; optional q8_kernels are required by create_transformer")
    elif precision and precision not in {"bfloat16", "mixed_precision"}:
        warnings.append(f"unrecognized precision {precision!r}; verify config before running")

    threshold = field_as_int(config, "prompt_enhancement_words_threshold")
    if threshold is not None:
        word_count = len(args.prompt.split())
        if threshold > 0 and word_count < threshold:
            warnings.append(
                "prompt enhancement will be active because prompt has "
                f"{word_count} words below threshold {threshold}; caption/LLM models may load"
            )
            for key in (
                "prompt_enhancer_image_caption_model_name_or_path",
                "prompt_enhancer_llm_model_name_or_path",
            ):
                ref = field_as_str(config, key)
                if ref and describe_model_reference(ref, config_path) != "local":
                    warnings.append(f"{key} is not a readable local path; prompt enhancement may use cache/network")
        elif threshold > 0:
            warnings.append(
                "prompt enhancement will be disabled for this run because prompt has "
                f"{word_count} words and threshold is {threshold}"
            )
        else:
            warnings.append("prompt enhancement threshold is <= 0; prompt enhancement is disabled")

    return errors, warnings, effective_strengths


def build_command(args: argparse.Namespace, effective_strengths: list[float] | None) -> list[str]:
    cmd = [
        "python",
        "inference.py",
        "--prompt",
        args.prompt,
        "--output_path",
        args.output_path,
        "--pipeline_config",
        args.pipeline_config,
        "--seed",
        str(args.seed),
        "--height",
        str(args.height),
        "--width",
        str(args.width),
        "--num_frames",
        str(args.num_frames),
        "--frame_rate",
        str(args.frame_rate),
        "--image_cond_noise_scale",
        str(args.image_cond_noise_scale),
    ]
    if args.negative_prompt:
        cmd.extend(["--negative_prompt", args.negative_prompt])
    if args.input_media_path:
        cmd.extend(["--input_media_path", args.input_media_path])
    if args.conditioning_media_paths:
        cmd.append("--conditioning_media_paths")
        cmd.extend(args.conditioning_media_paths)
        cmd.append("--conditioning_start_frames")
        cmd.extend(str(v) for v in args.conditioning_start_frames)
        cmd.append("--conditioning_strengths")
        cmd.extend(str(v) for v in (effective_strengths or []))
    if args.offload_to_cpu:
        cmd.append("--offload_to_cpu")
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings, effective_strengths = validate(args)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    print(shlex.join(build_command(args, effective_strengths)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

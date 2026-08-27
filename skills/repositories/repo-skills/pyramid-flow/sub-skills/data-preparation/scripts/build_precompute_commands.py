#!/usr/bin/env python3
"""Build validated Pyramid-Flow precompute command shapes.

This helper prints commands only. It does not launch torchrun, download
checkpoints, import Pyramid-Flow modules, or create output artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
from typing import Iterable, Sequence


TEXT_REQUIRED = ("text", "text_fea")
VAE_REQUIRED = ("video", "latent")
VALID_MODEL_NAMES = ("pyramid_flux", "pyramid_mmdit")
VALID_DTYPES = ("bf16", "fp16", "fp32")
KNOWN_RESOLUTIONS = {
    (640, 384): "384p",
    (1280, 768): "768p",
}


class CommandError(ValueError):
    """Readable user-facing validation failure."""


def read_jsonl(path: Path, limit: int) -> Iterable[tuple[int, dict]]:
    if not path.exists():
        raise CommandError(f"annotation file does not exist: {path}")
    if not path.is_file():
        raise CommandError(f"annotation path is not a file: {path}")

    seen = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise CommandError(f"row {line_number} is not valid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise CommandError(f"row {line_number} must be a JSON object")
            yield line_number, row
            seen += 1
            if limit and seen >= limit:
                break
    if seen == 0:
        raise CommandError(f"annotation file has no JSON rows: {path}")


def validate_jsonl_fields(path: Path, required: Sequence[str], label: str, limit: int) -> None:
    for line_number, row in read_jsonl(path, limit=limit):
        missing = [field for field in required if field not in row]
        if missing:
            raise CommandError(
                f"row {line_number} missing required field(s) for {label}: {', '.join(missing)}"
            )
        for field in required:
            if not isinstance(row[field], str) or not row[field].strip():
                raise CommandError(
                    f"row {line_number} field {field!r} for {label} must be a non-empty string"
                )


def validate_positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise CommandError(f"{name} must be a positive integer, got {value}")


def validate_checkpoint_arg(value: str, label: str) -> None:
    if not value or not value.strip():
        raise CommandError(f"{label} is required")
    stripped = value.strip()
    if stripped.startswith("<") or "PLACEHOLDER" in stripped.upper():
        raise CommandError(f"{label} still looks like a placeholder: {value}")


def validate_common(args: argparse.Namespace) -> None:
    validate_positive_int(args.gpus, "--gpus")
    validate_positive_int(args.batch_size, "--batch-size")
    if args.model_dtype not in VALID_DTYPES:
        raise CommandError(f"--model-dtype must be one of {', '.join(VALID_DTYPES)}")
    if not args.anno_file:
        raise CommandError("--anno-file is required")


def validate_vae_geometry(args: argparse.Namespace) -> None:
    validate_positive_int(args.width, "--width")
    validate_positive_int(args.height, "--height")
    validate_positive_int(args.num_frames, "--num-frames")
    if not args.allow_custom_resolution and (args.width, args.height) not in KNOWN_RESOLUTIONS:
        known = ", ".join(f"{w}x{h} ({name})" for (w, h), name in KNOWN_RESOLUTIONS.items())
        raise CommandError(
            f"unsupported width/height for stock LengthGroupedVideoTextDataset: "
            f"{args.width}x{args.height}; expected one of {known}. "
            "Pass --allow-custom-resolution only if the downstream loader has been changed."
        )
    if (args.num_frames - 1) % 8 != 0 and not args.allow_unaligned_frames:
        raise CommandError(
            f"--num-frames={args.num_frames} is not aligned to the VAE temporal pattern 8k+1; "
            "use 121 for 16 latent frames or pass --allow-unaligned-frames for custom code."
        )


def script_path(repo_root: str, relative: str) -> str:
    if repo_root in ("", "."):
        return relative
    return str(Path(repo_root) / relative)


def build_text_argv(args: argparse.Namespace) -> list[str]:
    validate_common(args)
    validate_checkpoint_arg(args.model_path, "--model-path")
    if args.model_name not in VALID_MODEL_NAMES:
        raise CommandError(f"--model-name must be one of {', '.join(VALID_MODEL_NAMES)}")
    if args.validate_annotations:
        validate_jsonl_fields(Path(args.anno_file), TEXT_REQUIRED, "text-features", args.validation_limit)
    return [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "tools/extract_text_features.py"),
        "--batch_size",
        str(args.batch_size),
        "--model_dtype",
        args.model_dtype,
        "--model_name",
        args.model_name,
        "--model_path",
        args.model_path,
        "--anno_file",
        args.anno_file,
    ]


def build_vae_argv(args: argparse.Namespace, *, model_path_attr: str = "model_path") -> list[str]:
    validate_common(args)
    model_path = getattr(args, model_path_attr)
    validate_checkpoint_arg(model_path, "--model-path" if model_path_attr == "model_path" else "--vae-model-path")
    validate_vae_geometry(args)
    if args.validate_annotations:
        validate_jsonl_fields(Path(args.anno_file), VAE_REQUIRED, "vae-latents", args.validation_limit)
    argv = [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "tools/extract_video_vae_latents.py"),
        "--batch_size",
        str(args.batch_size),
        "--model_dtype",
        args.model_dtype,
        "--model_path",
        model_path,
        "--anno_file",
        args.anno_file,
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--num_frames",
        str(args.num_frames),
    ]
    if args.save_memory:
        argv.append("--save_memory")
    return argv


def emit(commands: list[list[str]], output_format: str) -> None:
    if output_format == "json":
        payload = [{"argv": argv, "shell": shlex.join(argv)} for argv in commands]
        print(json.dumps(payload, indent=2))
    else:
        for argv in commands:
            print(shlex.join(argv))


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--gpus", type=int, default=8, help="Number of local processes for torchrun.")
    parser.add_argument("--batch-size", type=int, default=1, help="Precompute batch size; shell launchers use 1.")
    parser.add_argument("--model-dtype", choices=VALID_DTYPES, default="bf16", help="Model dtype passed to the extractor.")
    parser.add_argument("--anno-file", required=True, help="Annotation JSONL path for the precompute stage.")
    parser.add_argument("--repo-root", default=".", help="Prefix for repo-owned extractor paths in the emitted command.")
    parser.add_argument("--validate-annotations", action="store_true", help="Read a bounded sample of the JSONL and check required fields.")
    parser.add_argument("--validation-limit", type=int, default=100, help="Maximum non-empty JSONL rows to inspect when validating.")
    parser.add_argument("--format", choices=("shell", "json"), default="shell", help="Output command format.")


def add_vae_geometry_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--width", type=int, default=640, help="Raw video width for VAE extraction.")
    parser.add_argument("--height", type=int, default=384, help="Raw video height for VAE extraction.")
    parser.add_argument("--num-frames", type=int, default=121, help="Raw frames to encode; 121 maps to 16 latent frames.")
    parser.add_argument("--save-memory", action="store_true", help="Emit --save_memory to enable VAE tiling.")
    parser.add_argument("--allow-custom-resolution", action="store_true", help="Allow width/height outside the stock 384p and 768p loader shapes.")
    parser.add_argument("--allow-unaligned-frames", action="store_true", help="Allow num_frames values that are not 8k+1.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="workflow", required=True)

    text = subparsers.add_parser("text-features", help="Build a text-feature extraction command.")
    add_common_arguments(text)
    text.add_argument("--model-name", choices=VALID_MODEL_NAMES, default="pyramid_flux")
    text.add_argument("--model-path", required=True, help="Full Pyramid-Flow checkpoint directory matching --model-name.")

    vae = subparsers.add_parser("vae-latents", help="Build a video VAE latent extraction command.")
    add_common_arguments(vae)
    vae.add_argument("--model-path", required=True, help="Causal Video VAE checkpoint directory.")
    add_vae_geometry_arguments(vae)

    both = subparsers.add_parser("both", help="Build text-feature then VAE-latent extraction commands.")
    add_common_arguments(both)
    both.add_argument("--model-name", choices=VALID_MODEL_NAMES, default="pyramid_flux")
    both.add_argument("--model-path", required=True, help="Full Pyramid-Flow checkpoint directory for text features.")
    both.add_argument("--vae-model-path", required=True, help="Causal Video VAE checkpoint directory.")
    add_vae_geometry_arguments(both)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.workflow == "text-features":
            commands = [build_text_argv(args)]
        elif args.workflow == "vae-latents":
            commands = [build_vae_argv(args)]
        elif args.workflow == "both":
            if args.validate_annotations:
                validate_jsonl_fields(Path(args.anno_file), TEXT_REQUIRED, "text-features", args.validation_limit)
                validate_jsonl_fields(Path(args.anno_file), VAE_REQUIRED, "vae-latents", args.validation_limit)
            # Avoid double validation in the individual builders after combined validation.
            original_validate = args.validate_annotations
            args.validate_annotations = False
            try:
                commands = [build_text_argv(args), build_vae_argv(args, model_path_attr="vae_model_path")]
            finally:
                args.validate_annotations = original_validate
        else:  # pragma: no cover - argparse prevents this.
            raise CommandError(f"unknown workflow: {args.workflow}")
        emit(commands, args.format)
        return 0
    except CommandError as exc:
        print(f"COMMAND VALIDATION FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

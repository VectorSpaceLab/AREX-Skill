#!/usr/bin/env python3
"""Validate UniLM multimodal workflow inputs without running models.

This helper performs local path and argument checks for Kosmos, TextDiffuser,
audio/speech, and LatentLM workflows. It intentionally avoids importing torch,
fairseq, diffusers, transformers, PIL, or network clients.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}
CHECKPOINT_EXTENSIONS = {".pt", ".pth", ".bin", ".safetensors", ".ckpt"}
TEXTDIFFUSER1_MODES = {"text-to-image", "text-to-image-with-template", "text-inpainting"}
TEXTDIFFUSER2_VARIANTS = {"full", "lora", "inpainting", "train-full", "train-lora"}
TEXTDIFFUSER2_COORD_MODES = {"lt", "center", "ltrb"}
AUDIO_FAMILIES = {"wavlm", "beats", "speecht5", "speechlm", "valle"}
LATENTLM_OPERATIONS = {"sample", "sample-many", "train", "fid"}


def existing_path(value: str | None, label: str, *, required: bool = True) -> Path | None:
    if value is None or value == "":
        if required:
            raise ValueError(f"{label} is required")
        return None
    path = Path(value).expanduser()
    if not path.exists():
        raise ValueError(f"{label} does not exist: {value}")
    return path


def check_file(value: str | None, label: str, extensions: set[str] | None = None, *, required: bool = True) -> Path | None:
    path = existing_path(value, label, required=required)
    if path is None:
        return None
    if not path.is_file():
        raise ValueError(f"{label} must be a file: {value}")
    if extensions and path.suffix.lower() not in extensions:
        allowed = ", ".join(sorted(extensions))
        raise ValueError(f"{label} should have one of these extensions ({allowed}): {value}")
    return path


def check_dir(value: str | None, label: str, *, required: bool = True, create_ok: bool = False) -> Path | None:
    if value is None or value == "":
        if required:
            raise ValueError(f"{label} is required")
        return None
    path = Path(value).expanduser()
    if path.exists() and not path.is_dir():
        raise ValueError(f"{label} must be a directory: {value}")
    if not path.exists() and not create_ok:
        raise ValueError(f"{label} directory does not exist: {value}")
    return path


def looks_remote(value: str | None) -> bool:
    if not value:
        return False
    if value.startswith(("http://", "https://")):
        return True
    if value.startswith((".", "/", "~")):
        return False
    if Path(value).suffix:
        return False
    return bool(re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", value))


def validate_checkpoint_reference(value: str | None, label: str, *, allow_remote: bool = True, required: bool = True) -> None:
    if not value:
        if required:
            raise ValueError(f"{label} is required")
        return
    path = Path(value).expanduser()
    if path.exists():
        if path.is_file() and path.suffix.lower() not in CHECKPOINT_EXTENSIONS:
            raise ValueError(f"{label} has an unusual checkpoint extension: {value}")
        return
    if looks_remote(value):
        if not allow_remote:
            raise ValueError(f"{label} must be local for this mode: {value}")
        return
    raise ValueError(f"{label} does not exist: {value}")


def warn_if_output_exists(path_value: str | None, warnings: list[str], label: str = "output directory") -> None:
    if not path_value:
        return
    path = Path(path_value).expanduser()
    if path.exists() and path.is_dir() and any(path.iterdir()):
        warnings.append(f"{label} already exists and is non-empty: {path_value}")


def parse_span(value: str, label: str) -> list[float]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be JSON list syntax such as '[1.5, 5]'") from exc
    if not isinstance(parsed, list) or len(parsed) != 2:
        raise ValueError(f"{label} must contain exactly two numbers")
    numbers: list[float] = []
    for item in parsed:
        if not isinstance(item, (int, float)):
            raise ValueError(f"{label} values must be numeric")
        numbers.append(float(item))
    if numbers[0] >= numbers[1]:
        raise ValueError(f"{label} lower bound must be smaller than upper bound")
    return numbers


def require_prompt(prompt: str | None, label: str = "prompt") -> None:
    if prompt is None or prompt.strip() == "":
        raise ValueError(f"{label} is required and must not be empty")


def validate_image(path_value: str | None, label: str = "image", *, required: bool = True) -> None:
    check_file(path_value, label, IMAGE_EXTENSIONS, required=required)


def validate_audio_file(path_value: str | None, label: str = "audio", *, required: bool = True) -> None:
    check_file(path_value, label, AUDIO_EXTENSIONS, required=required)


def validate_imagefolder(path_value: str | None, label: str, warnings: list[str], *, required: bool = True) -> None:
    root = check_dir(path_value, label, required=required)
    if root is None:
        return
    class_dirs = [child for child in root.iterdir() if child.is_dir()]
    if not class_dirs:
        raise ValueError(f"{label} should use ImageFolder layout with one subdirectory per class: {path_value}")
    with_images = []
    for class_dir in class_dirs[:20]:
        if any(file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS for file in class_dir.rglob("*")):
            with_images.append(class_dir.name)
    if not with_images:
        warnings.append(f"{label} has class directories but no common image extensions found in the first 20 classes")


def add_common_status(summary: dict[str, object], warnings: list[str], checklist: list[str]) -> None:
    summary["warnings"] = warnings
    summary["safe_next_steps"] = checklist


def validate_kosmos2(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    validate_checkpoint_reference(args.checkpoint, "Kosmos-2 checkpoint", allow_remote=True)
    validate_image(args.image, required=args.image is not None)
    if args.image is None and args.prompt:
        warnings.append("prompt was provided without --image; fairseq dataset mode may ignore a single prompt")
    if args.image is not None:
        require_prompt(args.prompt)
    check_dir(args.output_dir, "output directory", create_ok=True)
    warn_if_output_exists(args.output_dir, warnings)
    checklist = [
        "Run native Kosmos-2 commands only from a compatible source checkout with fairseq and user-dir modules installed.",
        "Confirm checkpoint/tokenizer/dictionary paths and task-specific data root before using generate.py.",
        "Ask before downloading Kosmos weights, GRIT data, or evaluation datasets.",
        "For grounding outputs, verify decoded boxes against the image before treating them as ground truth.",
    ]
    summary: dict[str, object] = {"mode": "kosmos2", "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def validate_kosmos25(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    if args.task not in {"ocr", "markdown"}:
        raise ValueError("--task must be 'ocr' or 'markdown'")
    validate_image(args.image)
    validate_checkpoint_reference(args.checkpoint, "Kosmos-2.5 checkpoint", allow_remote=False)
    check_dir(args.output_dir, "output directory", create_ok=True)
    warn_if_output_exists(args.output_dir, warnings)
    if args.use_preprocess:
        parse_span(args.hw_ratio_adj_upper_span, "--hw-ratio-adj-upper-span")
        parse_span(args.hw_ratio_adj_lower_span, "--hw-ratio-adj-lower-span")
    checklist = [
        f"Use native {'--do_ocr' if args.task == 'ocr' else '--do_md'} and do not pass both task flags.",
        "Confirm the environment has Kosmos-2.5 forked fairseq/torchscale/transformers packages plus compatible FlashAttention2.",
        "Confirm GPU architecture is Ampere, Ada, or Hopper for the documented FlashAttention2 path.",
        "Inspect OCR/markdown output manually because Kosmos-2.5 is generative and may hallucinate.",
    ]
    summary: dict[str, object] = {"mode": "kosmos25", "task": args.task, "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def validate_textdiffuser1(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    if args.mode not in TEXTDIFFUSER1_MODES:
        raise ValueError(f"--mode must be one of: {', '.join(sorted(TEXTDIFFUSER1_MODES))}")
    require_prompt(args.prompt)
    validate_checkpoint_reference(args.checkpoint, "TextDiffuser checkpoint", allow_remote=True)
    if args.mode == "text-to-image-with-template":
        validate_image(args.template_image, "template image")
    if args.mode == "text-inpainting":
        validate_image(args.original_image, "original image")
        validate_image(args.text_mask, "text mask")
    check_dir(args.output_dir, "output directory", create_ok=True)
    warn_if_output_exists(args.output_dir, warnings)
    if args.font_path:
        check_file(args.font_path, "font file", {".ttf", ".otf"})
    if args.mode == "text-to-image" and "'" not in args.prompt:
        warnings.append("TextDiffuser v1 prompt-only rendering works best when target text is enclosed in single quotes")
    checklist = [
        "Run v1 native inference.py from the TextDiffuser source checkout with diffusers, accelerate, and compatible Torch/CUDA.",
        "Verify checkpoint archive includes the diffusion backbone and related text/layout components.",
        "Ask before downloading the large checkpoint archive, MARIO data, fonts, or OCR metric dependencies.",
        "Lower --vis_num or sample steps first if CUDA memory is tight.",
    ]
    summary: dict[str, object] = {"mode": "textdiffuser1", "td_mode": args.mode, "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def validate_textdiffuser2(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    if args.variant not in TEXTDIFFUSER2_VARIANTS:
        raise ValueError(f"--variant must be one of: {', '.join(sorted(TEXTDIFFUSER2_VARIANTS))}")
    if args.coord_mode not in TEXTDIFFUSER2_COORD_MODES:
        raise ValueError(f"--coord-mode must be one of: {', '.join(sorted(TEXTDIFFUSER2_COORD_MODES))}")
    if not (1 <= args.granularity <= 512):
        raise ValueError("--granularity must be between 1 and 512")
    check_dir(args.output_dir, "output directory", create_ok=True)
    warn_if_output_exists(args.output_dir, warnings)

    if args.variant in {"full", "lora"}:
        validate_checkpoint_reference(args.checkpoint, "TextDiffuser-2 checkpoint", allow_remote=True)
        validate_checkpoint_reference(args.layout_model, "TextDiffuser-2 layout planner", allow_remote=True)
        if args.input_file:
            check_file(args.input_file, "input file", required=True)
        else:
            require_prompt(args.prompt, "prompt or --input-file")
    elif args.variant == "inpainting":
        validate_checkpoint_reference(args.checkpoint, "TextDiffuser-2 inpainting checkpoint", allow_remote=True)
        validate_image(args.original_image, "original image")
        validate_image(args.text_mask, "text mask")
        if not args.prompt and not args.input_file:
            warnings.append("inpainting usually needs text/layout instructions in addition to image and mask")
    else:
        if not args.dataset_path and not args.dataset_name:
            raise ValueError("training variants require --dataset-path or --dataset-name")
        if args.dataset_path:
            check_dir(args.dataset_path, "dataset path")
        if args.train_index:
            check_file(args.train_index, "train index file", {".txt", ".json", ".jsonl"})
        else:
            warnings.append("training variants usually require --index_file_path / --train_dataset_index_file")

    if args.variant == "lora" and args.checkpoint and "lora" not in args.checkpoint.lower():
        warnings.append("LoRA variant selected but checkpoint name does not mention LoRA; verify script/checkpoint pairing")
    if args.variant == "full" and args.checkpoint and "lora" in args.checkpoint.lower():
        warnings.append("Full variant selected but checkpoint name mentions LoRA; verify script/checkpoint pairing")
    checklist = [
        "Use full and LoRA checkpoints with their matching native inference scripts.",
        "Confirm accelerate config, Torch/CUDA, xformers, and optional FlashAttention before launching.",
        "Ask before Hugging Face downloads or demo asset downloads.",
        "Use coord_mode/granularity/max_length values aligned with the released checkpoint.",
    ]
    summary: dict[str, object] = {"mode": "textdiffuser2", "variant": args.variant, "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def validate_audio(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    if args.family not in AUDIO_FAMILIES:
        raise ValueError(f"--family must be one of: {', '.join(sorted(AUDIO_FAMILIES))}")
    if args.family == "valle":
        warnings.append("Inspected UniLM VALL-E evidence contains release/demo notes only; no local native script was present")
    else:
        validate_checkpoint_reference(args.checkpoint, f"{args.family} checkpoint", allow_remote=True)
    if args.audio:
        validate_audio_file(args.audio)
    if args.manifest:
        check_file(args.manifest, "manifest", {".tsv", ".txt", ".json", ".jsonl", ".csv"})
    if args.data_root:
        check_dir(args.data_root, "data root")
    if args.sample_rate != 16000:
        warnings.append("UniLM WavLM/BEATs/SpeechT5/SpeechLM evidence assumes 16 kHz audio")
    if args.family in {"speecht5", "speechlm"} and not (args.manifest or args.data_root):
        warnings.append("fairseq speech workflows usually require a manifest/data root, not only a single audio file")
    checklist = [
        "Confirm audio is mono 16 kHz or resample before feature extraction/generation.",
        "Inspect checkpoint keys privately for cfg/model/label_dict compatibility before loading into source classes.",
        "For SpeechT5/SpeechLM, verify fairseq user-dir, labels, BPE/dictionary, subset names, and batch-size constraints.",
        "Do not fabricate VALL-E commands from this checkout; request an implementation if needed.",
    ]
    summary: dict[str, object] = {"mode": "audio", "family": args.family, "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def validate_latentlm(args: argparse.Namespace) -> dict[str, object]:
    warnings: list[str] = []
    if args.operation not in LATENTLM_OPERATIONS:
        raise ValueError(f"--operation must be one of: {', '.join(sorted(LATENTLM_OPERATIONS))}")
    checkpoint_dir = None
    if args.operation in {"sample", "sample-many", "fid"} or args.checkpoint:
        checkpoint_dir = check_dir(args.checkpoint, "checkpoint directory")
        has_model = (
            (checkpoint_dir / "model.safetensors").is_file()
            or (checkpoint_dir / "pytorch_model" / "mp_rank_00_model_states.pt").is_file()
        )
        if not has_model:
            warnings.append("checkpoint directory lacks model.safetensors or pytorch_model/mp_rank_00_model_states.pt")
        if not (checkpoint_dir / "other_state.pth").is_file():
            warnings.append("checkpoint directory lacks other_state.pth; sampling/evaluation or EMA may fail")
    if args.vae:
        validate_checkpoint_reference(args.vae, "VAE", allow_remote=True, required=False)
    elif args.operation in {"sample", "sample-many", "train", "fid"}:
        warnings.append("--vae is not set; native scripts may rely on defaults or fail if VAE is required")

    if args.operation == "train":
        if not args.dataset_name and not args.train_data_dir:
            raise ValueError("LatentLM training requires --dataset-name or --train-data-dir")
        if args.train_data_dir:
            validate_imagefolder(args.train_data_dir, "train data directory", warnings)
        check_dir(args.output_dir, "output directory", create_ok=True)
        warn_if_output_exists(args.output_dir, warnings)
    elif args.operation == "fid":
        check_file(args.ref_stat, "reference FID stats", {".npz"})
        if args.train_data_dir:
            validate_imagefolder(args.train_data_dir, "train data directory", warnings, required=False)
        if checkpoint_dir:
            warnings.append("native FID evaluation writes cached latents/results/images into the checkpoint directory")
    elif args.operation == "sample":
        if args.output_dir:
            check_dir(args.output_dir, "output directory", create_ok=True)
            warn_if_output_exists(args.output_dir, warnings)
        if args.image_name and Path(args.image_name).suffix.lower() not in IMAGE_EXTENSIONS:
            warnings.append("--image-name should usually end in an image extension such as .png")
    elif args.operation == "sample-many":
        if args.batch_size < 1:
            raise ValueError("--batch-size must be positive")
        warnings.append("native sample_many.py writes images to demo/ unless adapted")

    if args.num_classes < 1:
        raise ValueError("--num-classes must be positive")
    checklist = [
        "Confirm LatentLM script operation matches checkpoint layout and model config.",
        "Ask before Hugging Face dataset/model downloads or using remote VAE identifiers.",
        "Use ImageFolder class subdirectories for local training data and align --num-classes with labels.",
        "Run FID on a scratch checkpoint copy if cached latents/results should not mutate the original checkpoint.",
    ]
    summary: dict[str, object] = {"mode": "latentlm", "operation": args.operation, "status": "ok"}
    add_common_status(summary, warnings, checklist)
    return summary


def print_summary(summary: dict[str, object]) -> None:
    print(json.dumps(summary, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate UniLM multimodal workflow inputs without importing heavy model frameworks or running generation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    kosmos2 = subparsers.add_parser("kosmos2", help="Validate Kosmos-2 grounding/generation planning inputs")
    kosmos2.add_argument("--checkpoint", required=True, help="Local checkpoint path or approved remote model reference")
    kosmos2.add_argument("--image", help="Optional local image for single-image planning")
    kosmos2.add_argument("--prompt", help="Prompt for single-image planning")
    kosmos2.add_argument("--output-dir", required=True, help="Output directory to create/use")
    kosmos2.set_defaults(func=validate_kosmos2)

    kosmos25 = subparsers.add_parser("kosmos25", help="Validate Kosmos-2.5 OCR or markdown inputs")
    kosmos25.add_argument("--task", choices=["ocr", "markdown"], required=True)
    kosmos25.add_argument("--image", required=True)
    kosmos25.add_argument("--checkpoint", required=True)
    kosmos25.add_argument("--output-dir", required=True)
    kosmos25.add_argument("--use-preprocess", action="store_true")
    kosmos25.add_argument("--hw-ratio-adj-upper-span", default="[1.5, 5]")
    kosmos25.add_argument("--hw-ratio-adj-lower-span", default="[0.5, 1.0]")
    kosmos25.set_defaults(func=validate_kosmos25)

    td1 = subparsers.add_parser("textdiffuser1", help="Validate TextDiffuser v1 inference/eval inputs")
    td1.add_argument("--mode", choices=sorted(TEXTDIFFUSER1_MODES), required=True)
    td1.add_argument("--prompt", required=True)
    td1.add_argument("--checkpoint", required=True)
    td1.add_argument("--template-image")
    td1.add_argument("--original-image")
    td1.add_argument("--text-mask")
    td1.add_argument("--font-path")
    td1.add_argument("--output-dir", required=True)
    td1.set_defaults(func=validate_textdiffuser1)

    td2 = subparsers.add_parser("textdiffuser2", help="Validate TextDiffuser-2 inference/training inputs")
    td2.add_argument("--variant", choices=sorted(TEXTDIFFUSER2_VARIANTS), required=True)
    td2.add_argument("--prompt")
    td2.add_argument("--input-file")
    td2.add_argument("--checkpoint")
    td2.add_argument("--layout-model")
    td2.add_argument("--original-image")
    td2.add_argument("--text-mask")
    td2.add_argument("--dataset-path")
    td2.add_argument("--dataset-name")
    td2.add_argument("--train-index")
    td2.add_argument("--output-dir", required=True)
    td2.add_argument("--coord-mode", default="ltrb", choices=sorted(TEXTDIFFUSER2_COORD_MODES))
    td2.add_argument("--granularity", type=int, default=128)
    td2.set_defaults(func=validate_textdiffuser2)

    audio = subparsers.add_parser("audio", help="Validate WavLM/BEATs/SpeechT5/SpeechLM/VALL-E inputs")
    audio.add_argument("--family", choices=sorted(AUDIO_FAMILIES), required=True)
    audio.add_argument("--checkpoint")
    audio.add_argument("--audio")
    audio.add_argument("--manifest")
    audio.add_argument("--data-root")
    audio.add_argument("--sample-rate", type=int, default=16000)
    audio.set_defaults(func=validate_audio)

    latent = subparsers.add_parser("latentlm", help="Validate LatentLM sampling/training/FID inputs")
    latent.add_argument("--operation", choices=sorted(LATENTLM_OPERATIONS), required=True)
    latent.add_argument("--checkpoint")
    latent.add_argument("--vae")
    latent.add_argument("--train-data-dir")
    latent.add_argument("--dataset-name")
    latent.add_argument("--ref-stat")
    latent.add_argument("--output-dir")
    latent.add_argument("--image-name", default="sample.png")
    latent.add_argument("--batch-size", type=int, default=32)
    latent.add_argument("--num-classes", type=int, default=1000)
    latent.set_defaults(func=validate_latentlm)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = args.func(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

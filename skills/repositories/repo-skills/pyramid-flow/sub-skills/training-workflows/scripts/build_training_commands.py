#!/usr/bin/env python3
"""Build validated Pyramid-Flow training command shapes.

This helper prints commands only. It does not launch torchrun, download
checkpoints, import Pyramid-Flow modules, or create output artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
from typing import Sequence


VALID_MODEL_NAMES = ("pyramid_flux", "pyramid_mmdit")
VALID_DIT_VARIANTS = (
    "diffusion_transformer_384p",
    "diffusion_transformer_768p",
    "diffusion_transformer_image",
)
VALID_DIT_RESOLUTIONS = ("384p", "768p")
VALID_DTYPES = ("bf16", "fp16")
VALID_FSDP_SHARDS = ("zero2", "zero3")
VALID_VAE_STAGES = ("stage1", "stage2", "both")


class CommandError(ValueError):
    """Readable user-facing validation failure."""


def script_path(repo_root: str, relative: str) -> str:
    if repo_root in ("", ".", "./"):
        return relative
    return str(Path(repo_root) / relative)


def validate_positive_int(value: int, label: str) -> None:
    if value <= 0:
        raise CommandError(f"{label} must be a positive integer, got {value}")


def validate_nonnegative_int(value: int, label: str) -> None:
    if value < 0:
        raise CommandError(f"{label} must be non-negative, got {value}")


def validate_ratio(value: float, label: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise CommandError(f"{label} must be between 0.0 and 1.0, got {value}")


def validate_required_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CommandError(f"{label} is required")
    stripped = value.strip()
    upper = stripped.upper()
    if stripped.startswith("<") or "PLACEHOLDER" in upper or stripped in {"/PATH", "PATH"}:
        raise CommandError(f"{label} still looks like a placeholder: {value}")


def validate_choice(value: str, choices: Sequence[str], label: str) -> None:
    if value not in choices:
        raise CommandError(f"{label} must be one of {', '.join(choices)}, got {value}")


def validate_dit_common(args: argparse.Namespace, *, workflow: str) -> None:
    validate_positive_int(args.gpus, "--gpus")
    validate_positive_int(args.batch_size, "--batch-size")
    validate_positive_int(args.num_frames, "--num-frames")
    validate_positive_int(args.num_workers, "--num-workers")
    validate_positive_int(args.gradient_accumulation_steps, "--gradient-accumulation-steps")
    validate_nonnegative_int(args.seed, "--seed")
    validate_choice(args.model_name, VALID_MODEL_NAMES, "--model-name")
    validate_choice(args.model_variant, VALID_DIT_VARIANTS, "--model-variant")
    validate_choice(args.model_dtype, VALID_DTYPES, "--model-dtype")
    validate_choice(args.fsdp_shard_strategy, VALID_FSDP_SHARDS, "--fsdp-shard-strategy")
    validate_choice(args.resolution, VALID_DIT_RESOLUTIONS, "--resolution")
    validate_required_text(args.model_path, "--model-path")
    validate_required_text(args.output_dir, "--output-dir")
    validate_required_text(args.anno_file, "--anno-file")

    if args.batch_size % 4 != 0:
        raise CommandError(
            f"DiT --batch-size must be divisible by 4 because train_pyramid_flow.py "
            f"uses sample_ratios=[1, 2, 1]; got {args.batch_size}"
        )

    if args.use_sequence_parallel:
        validate_positive_int(args.sp_group_size, "--sp-group-size")
        if args.sp_group_size <= 1:
            raise CommandError("--sp-group-size must be > 1 when --use-sequence-parallel is set")
        if args.sp_proc_num != -1:
            validate_positive_int(args.sp_proc_num, "--sp-proc-num")
            if args.sp_proc_num % args.sp_group_size != 0:
                raise CommandError("--sp-proc-num must be divisible by --sp-group-size")

    if workflow == "pyramid-flow-ar":
        validate_positive_int(args.video_sync_group, "--video-sync-group")
        if args.gpus % args.video_sync_group != 0:
            raise CommandError(
                f"GPUS % VIDEO_SYNC_GROUP must be 0 for synchronized AR video input; "
                f"got {args.gpus} % {args.video_sync_group}"
            )
        if args.num_frames % args.video_sync_group != 0:
            raise CommandError(
                f"NUM_FRAMES % VIDEO_SYNC_GROUP must be 0 for AR training; "
                f"got {args.num_frames} % {args.video_sync_group}"
            )
        if args.model_variant == "diffusion_transformer_image":
            raise CommandError("the AR video launcher must use a video DiT variant, not diffusion_transformer_image")
        if args.resolution == "384p" and args.model_variant == "diffusion_transformer_768p":
            raise CommandError("384p AR training should use diffusion_transformer_384p")
        if args.resolution == "768p" and args.model_variant == "diffusion_transformer_384p":
            raise CommandError("768p AR training should use diffusion_transformer_768p")
    elif workflow == "pyramid-flow-no-ar":
        if args.model_variant != "diffusion_transformer_image":
            raise CommandError(
                "the published non-AR launcher is the t2i image-training path and uses "
                "diffusion_transformer_image"
            )
        if args.resolution != "768p":
            raise CommandError("the published non-AR t2i launcher uses resolution=768p")


def validate_vae_common(args: argparse.Namespace) -> None:
    validate_choice(args.stage, VALID_VAE_STAGES, "--stage")
    validate_positive_int(args.gpus, "--gpus")
    validate_positive_int(args.resolution, "--resolution")
    validate_positive_int(args.num_workers, "--num-workers")
    validate_choice(args.model_dtype, VALID_DTYPES, "--model-dtype")
    validate_required_text(args.vae_model_path, "--vae-model-path")
    validate_required_text(args.lpips_ckpt, "--lpips-ckpt")
    validate_required_text(args.output_dir, "--output-dir")
    validate_required_text(args.video_anno, "--video-anno")

    if args.stage in ("stage1", "both"):
        validate_required_text(args.image_anno, "--image-anno")
        validate_positive_int(args.stage1_batch_size, "--stage1-batch-size")
        validate_positive_int(args.stage1_num_frames, "--stage1-num-frames")
        validate_ratio(args.image_mix_ratio, "--image-mix-ratio")
        if args.stage1_num_frames != 17:
            raise CommandError("VAE stage-1 uses --stage1-num-frames=17 in the published training recipe")

    if args.stage in ("stage2", "both"):
        validate_required_text(args.pretrained_vae_weight, "--pretrained-vae-weight")
        validate_positive_int(args.stage2_batch_size, "--stage2-batch-size")
        validate_positive_int(args.context_size, "--context-size")
        validate_positive_int(args.stage2_num_frames, "--stage2-num-frames")
        if args.gpus % args.context_size != 0:
            raise CommandError(
                f"GPUS % CONTEXT_SIZE must be 0 for VAE context parallel; "
                f"got {args.gpus} % {args.context_size}"
            )
        expected_frames = 16 * args.context_size + 1
        if args.stage2_num_frames != expected_frames:
            raise CommandError(
                f"stage-2 NUM_FRAMES must be (17 - 1) * CONTEXT_SIZE + 1; "
                f"got {args.stage2_num_frames}, expected {expected_frames}"
            )


def append_optional_sequence_parallel(argv: list[str], args: argparse.Namespace) -> None:
    if args.use_sequence_parallel:
        argv.extend(["--use_sequence_parallel", "--sp_group_size", str(args.sp_group_size)])
        if args.sp_proc_num != -1:
            argv.extend(["--sp_proc_num", str(args.sp_proc_num)])


def build_pyramid_flow_ar_argv(args: argparse.Namespace) -> list[str]:
    validate_dit_common(args, workflow="pyramid-flow-ar")
    argv = [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "train/train_pyramid_flow.py"),
        "--num_workers",
        str(args.num_workers),
        "--task",
        "t2v",
        "--use_fsdp",
        "--fsdp_shard_strategy",
        args.fsdp_shard_strategy,
        "--use_temporal_causal",
        "--use_temporal_pyramid",
        "--interp_condition_pos",
        "--sync_video_input",
        "--video_sync_group",
        str(args.video_sync_group),
        "--load_text_encoder",
        "--model_name",
        args.model_name,
        "--model_path",
        args.model_path,
        "--model_dtype",
        args.model_dtype,
        "--model_variant",
        args.model_variant,
        "--schedule_shift",
        "1.0",
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--output_dir",
        args.output_dir,
        "--batch_size",
        str(args.batch_size),
        "--max_frames",
        str(args.num_frames),
        "--resolution",
        args.resolution,
        "--anno_file",
        args.anno_file,
        "--frame_per_unit",
        "1",
        "--lr_scheduler",
        "constant_with_warmup",
        "--opt",
        "adamw",
        "--opt_beta1",
        "0.9",
        "--opt_beta2",
        "0.95",
        "--seed",
        str(args.seed),
        "--weight_decay",
        "1e-4",
        "--clip_grad",
        "1.0",
        "--lr",
        str(args.lr),
        "--warmup_steps",
        "1000",
        "--epochs",
        str(args.epochs),
        "--iters_per_epoch",
        str(args.iters_per_epoch),
        "--report_to",
        "tensorboard",
        "--print_freq",
        "40",
        "--save_ckpt_freq",
        "1",
    ]
    if args.gradient_checkpointing:
        argv.append("--gradient_checkpointing")
    append_optional_sequence_parallel(argv, args)
    return argv


def build_pyramid_flow_no_ar_argv(args: argparse.Namespace) -> list[str]:
    validate_dit_common(args, workflow="pyramid-flow-no-ar")
    argv = [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "train/train_pyramid_flow.py"),
        "--num_workers",
        str(args.num_workers),
        "--task",
        "t2i",
        "--use_fsdp",
        "--fsdp_shard_strategy",
        args.fsdp_shard_strategy,
        "--use_flash_attn",
        "--load_text_encoder",
        "--load_vae",
        "--model_name",
        args.model_name,
        "--model_path",
        args.model_path,
        "--model_dtype",
        args.model_dtype,
        "--model_variant",
        args.model_variant,
        "--schedule_shift",
        "1.0",
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--output_dir",
        args.output_dir,
        "--batch_size",
        str(args.batch_size),
        "--max_frames",
        str(args.num_frames),
        "--resolution",
        args.resolution,
        "--anno_file",
        args.anno_file,
        "--frame_per_unit",
        "1",
        "--lr_scheduler",
        "constant_with_warmup",
        "--opt",
        "adamw",
        "--opt_beta1",
        "0.9",
        "--opt_beta2",
        "0.95",
        "--seed",
        str(args.seed),
        "--weight_decay",
        "1e-4",
        "--clip_grad",
        "1.0",
        "--lr",
        str(args.lr),
        "--warmup_steps",
        "1000",
        "--epochs",
        str(args.epochs),
        "--iters_per_epoch",
        str(args.iters_per_epoch),
        "--report_to",
        "tensorboard",
        "--print_freq",
        "40",
        "--save_ckpt_freq",
        "1",
    ]
    if args.gradient_checkpointing:
        argv.append("--gradient_checkpointing")
    append_optional_sequence_parallel(argv, args)
    return argv


def build_vae_stage1_argv(args: argparse.Namespace) -> list[str]:
    return [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "train/train_video_vae.py"),
        "--num_workers",
        str(args.num_workers),
        "--model_path",
        args.vae_model_path,
        "--model_dtype",
        args.model_dtype,
        "--lpips_ckpt",
        args.lpips_ckpt,
        "--output_dir",
        args.output_dir,
        "--image_anno",
        args.image_anno,
        "--video_anno",
        args.video_anno,
        "--use_image_video_mixed_training",
        "--image_mix_ratio",
        str(args.image_mix_ratio),
        "--resolution",
        str(args.resolution),
        "--max_frames",
        str(args.stage1_num_frames),
        "--disc_start",
        "250000",
        "--kl_weight",
        "1e-12",
        "--pixelloss_weight",
        "10.0",
        "--perceptual_weight",
        "1.0",
        "--disc_weight",
        "0.5",
        "--batch_size",
        str(args.stage1_batch_size),
        "--opt",
        "adamw",
        "--opt_betas",
        "0.9",
        "0.95",
        "--seed",
        str(args.seed),
        "--weight_decay",
        "1e-3",
        "--clip_grad",
        "1.0",
        "--lr",
        str(args.lr),
        "--lr_disc",
        str(args.lr_disc),
        "--warmup_epochs",
        "1",
        "--epochs",
        str(args.epochs),
        "--iters_per_epoch",
        str(args.iters_per_epoch),
        "--print_freq",
        "40",
        "--save_ckpt_freq",
        "1",
    ]


def build_vae_stage2_argv(args: argparse.Namespace) -> list[str]:
    return [
        "torchrun",
        "--nproc_per_node",
        str(args.gpus),
        script_path(args.repo_root, "train/train_video_vae.py"),
        "--num_workers",
        str(args.num_workers),
        "--model_path",
        args.vae_model_path,
        "--model_dtype",
        args.model_dtype,
        "--pretrained_vae_weight",
        args.pretrained_vae_weight,
        "--use_context_parallel",
        "--context_size",
        str(args.context_size),
        "--lpips_ckpt",
        args.lpips_ckpt,
        "--output_dir",
        args.output_dir,
        "--video_anno",
        args.video_anno,
        "--image_mix_ratio",
        "0.0",
        "--resolution",
        str(args.resolution),
        "--max_frames",
        str(args.stage2_num_frames),
        "--disc_start",
        "250000",
        "--kl_weight",
        "1e-12",
        "--pixelloss_weight",
        "10.0",
        "--perceptual_weight",
        "1.0",
        "--disc_weight",
        "0.5",
        "--batch_size",
        str(args.stage2_batch_size),
        "--opt",
        "adamw",
        "--opt_betas",
        "0.9",
        "0.95",
        "--seed",
        str(args.seed),
        "--weight_decay",
        "1e-3",
        "--clip_grad",
        "1.0",
        "--lr",
        str(args.lr),
        "--lr_disc",
        str(args.lr_disc),
        "--warmup_epochs",
        "1",
        "--epochs",
        str(args.epochs),
        "--iters_per_epoch",
        str(args.iters_per_epoch),
        "--print_freq",
        "40",
        "--save_ckpt_freq",
        "1",
    ]


def build_causal_video_vae_argvs(args: argparse.Namespace) -> list[list[str]]:
    validate_vae_common(args)
    commands: list[list[str]] = []
    if args.stage in ("stage1", "both"):
        commands.append(build_vae_stage1_argv(args))
    if args.stage in ("stage2", "both"):
        commands.append(build_vae_stage2_argv(args))
    return commands


def emit(commands: list[list[str]], output_format: str) -> None:
    if output_format == "json":
        payload = [{"argv": argv, "shell": shlex.join(argv)} for argv in commands]
        print(json.dumps(payload, indent=2))
    else:
        for index, argv in enumerate(commands):
            if index:
                print()
            print(shlex.join(argv))


def add_common_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", default=".", help="Prefix for repo-owned training script paths in emitted commands.")
    parser.add_argument("--format", choices=("shell", "json"), default="shell", help="Output command format.")


def add_common_dit_arguments(parser: argparse.ArgumentParser, *, default_batch_size: int, default_num_frames: int, default_resolution: str, default_variant: str, default_lr: str, default_grad_accum: int) -> None:
    parser.add_argument("--gpus", type=int, default=8, help="Number of local processes for torchrun.")
    parser.add_argument("--model-name", choices=VALID_MODEL_NAMES, default="pyramid_flux")
    parser.add_argument("--model-path", required=True, help="Checkpoint directory matching --model-name and --model-variant.")
    parser.add_argument("--model-variant", choices=VALID_DIT_VARIANTS, default=default_variant)
    parser.add_argument("--model-dtype", choices=VALID_DTYPES, default="bf16")
    parser.add_argument("--fsdp-shard-strategy", choices=VALID_FSDP_SHARDS, default="zero2")
    parser.add_argument("--output-dir", required=True, help="Directory for checkpoints and logs.")
    parser.add_argument("--anno-file", required=True, help="Training annotation JSONL path.")
    parser.add_argument("--batch-size", type=int, default=default_batch_size, help="Per-device batch size.")
    parser.add_argument("--num-frames", type=int, default=default_num_frames, help="Maximum latent/video frame count passed as --max_frames.")
    parser.add_argument("--resolution", choices=VALID_DIT_RESOLUTIONS, default=default_resolution)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=default_grad_accum)
    parser.add_argument("--gradient-checkpointing", action="store_true", help="Append --gradient_checkpointing; recommended for 768p variants.")
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--lr", default=default_lr, help="Learning rate to pass through to train/train_pyramid_flow.py.")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--iters-per-epoch", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-sequence-parallel", action="store_true", help="Append optional trainer_misc sequence-parallel flags.")
    parser.add_argument("--sp-group-size", type=int, default=1)
    parser.add_argument("--sp-proc-num", type=int, default=-1, help="-1 means all torchrun processes, matching the source default.")
    add_common_output_arguments(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="workflow", required=True)

    ar = subparsers.add_parser("pyramid-flow-ar", help="Build the autoregressive temporal-pyramid DiT video training command.")
    add_common_dit_arguments(
        ar,
        default_batch_size=4,
        default_num_frames=16,
        default_resolution="384p",
        default_variant="diffusion_transformer_384p",
        default_lr="5e-5",
        default_grad_accum=2,
    )
    ar.add_argument("--video-sync-group", type=int, default=8, help="Ranks that share the same input video in AR training.")

    no_ar = subparsers.add_parser("pyramid-flow-no-ar", help="Build the published non-AR/full-sequence t2i DiT training command.")
    add_common_dit_arguments(
        no_ar,
        default_batch_size=4,
        default_num_frames=8,
        default_resolution="768p",
        default_variant="diffusion_transformer_image",
        default_lr="1e-4",
        default_grad_accum=1,
    )

    vae = subparsers.add_parser("causal-video-vae", help="Build Causal Video VAE stage-1, stage-2, or two-stage commands.")
    vae.add_argument("--stage", choices=VALID_VAE_STAGES, default="both")
    vae.add_argument("--gpus", type=int, default=8, help="Number of local processes for torchrun.")
    vae.add_argument("--vae-model-path", required=True, help="Base Causal Video VAE checkpoint/model directory.")
    vae.add_argument("--model-dtype", choices=VALID_DTYPES, default="bf16")
    vae.add_argument("--lpips-ckpt", required=True, help="LPIPS VGG checkpoint file; must be downloaded/provided by the user.")
    vae.add_argument("--output-dir", required=True, help="Directory for checkpoints and logs.")
    vae.add_argument("--image-anno", default="", help="Image JSONL annotation for stage-1 mixed training.")
    vae.add_argument("--video-anno", required=True, help="Video JSONL annotation for VAE training.")
    vae.add_argument("--pretrained-vae-weight", default="", help="Stage-1 checkpoint path required for stage-2.")
    vae.add_argument("--resolution", type=int, default=256, help="VAE training spatial resolution.")
    vae.add_argument("--stage1-num-frames", type=int, default=17)
    vae.add_argument("--stage2-num-frames", type=int, default=33)
    vae.add_argument("--context-size", type=int, default=2, help="Context-parallel size for stage-2.")
    vae.add_argument("--stage1-batch-size", type=int, default=2)
    vae.add_argument("--stage2-batch-size", type=int, default=2)
    vae.add_argument("--image-mix-ratio", type=float, default=0.1)
    vae.add_argument("--num-workers", type=int, default=6)
    vae.add_argument("--lr", default="1e-4")
    vae.add_argument("--lr-disc", default="1e-4")
    vae.add_argument("--epochs", type=int, default=100)
    vae.add_argument("--iters-per-epoch", type=int, default=2000)
    vae.add_argument("--seed", type=int, default=42)
    add_common_output_arguments(vae)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.workflow == "pyramid-flow-ar":
            commands = [build_pyramid_flow_ar_argv(args)]
        elif args.workflow == "pyramid-flow-no-ar":
            commands = [build_pyramid_flow_no_ar_argv(args)]
        elif args.workflow == "causal-video-vae":
            commands = build_causal_video_vae_argvs(args)
        else:  # pragma: no cover - argparse prevents this.
            raise CommandError(f"unknown workflow: {args.workflow}")
        emit(commands, args.format)
        return 0
    except CommandError as exc:
        print(f"TRAINING COMMAND VALIDATION FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

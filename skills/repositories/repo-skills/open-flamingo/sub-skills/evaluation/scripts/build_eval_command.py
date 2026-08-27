#!/usr/bin/env python3
"""Print a validated OpenFlamingo evaluation or RICES-cache command.

This helper never executes the command. It only prints a shell string that can
be copied into a terminal.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

EVAL_DATASET_FLAGS = [
    "eval_coco",
    "eval_flickr30",
    "eval_vqav2",
    "eval_ok_vqa",
    "eval_vizwiz",
    "eval_textvqa",
    "eval_imagenet",
    "eval_hateful_memes",
]


EVAL_REQUIRED = {
    "eval_coco": [
        "coco_train_image_dir_path",
        "coco_val_image_dir_path",
        "coco_karpathy_json_path",
        "coco_annotations_json_path",
    ],
    "eval_flickr30": [
        "flickr_image_dir_path",
        "flickr_karpathy_json_path",
        "flickr_annotations_json_path",
    ],
    "eval_vqav2": [
        "vqav2_train_image_dir_path",
        "vqav2_train_questions_json_path",
        "vqav2_train_annotations_json_path",
        "vqav2_test_image_dir_path",
        "vqav2_test_questions_json_path",
    ],
    "eval_ok_vqa": [
        "ok_vqa_train_image_dir_path",
        "ok_vqa_train_questions_json_path",
        "ok_vqa_train_annotations_json_path",
        "ok_vqa_test_image_dir_path",
        "ok_vqa_test_questions_json_path",
        "ok_vqa_test_annotations_json_path",
    ],
    "eval_vizwiz": [
        "vizwiz_train_image_dir_path",
        "vizwiz_train_questions_json_path",
        "vizwiz_train_annotations_json_path",
        "vizwiz_test_image_dir_path",
        "vizwiz_test_questions_json_path",
    ],
    "eval_textvqa": [
        "textvqa_image_dir_path",
        "textvqa_train_questions_json_path",
        "textvqa_train_annotations_json_path",
        "textvqa_test_questions_json_path",
        "textvqa_test_annotations_json_path",
    ],
    "eval_imagenet": ["imagenet_root"],
    "eval_hateful_memes": [
        "hateful_memes_image_dir_path",
        "hateful_memes_train_annotations_json_path",
        "hateful_memes_test_annotations_json_path",
    ],
}

CACHE_REQUIRED = {
    "eval_coco": [
        "coco_train_image_dir_path",
        "coco_val_image_dir_path",
        "coco_karpathy_json_path",
        "coco_annotations_json_path",
    ],
    "eval_flickr30": [
        "flickr_image_dir_path",
        "flickr_karpathy_json_path",
        "flickr_annotations_json_path",
    ],
    "eval_vqav2": [
        "vqav2_train_image_dir_path",
        "vqav2_train_questions_json_path",
        "vqav2_train_annotations_json_path",
    ],
    "eval_ok_vqa": [
        "ok_vqa_train_image_dir_path",
        "ok_vqa_train_questions_json_path",
        "ok_vqa_train_annotations_json_path",
    ],
    "eval_vizwiz": [
        "vizwiz_train_image_dir_path",
        "vizwiz_train_questions_json_path",
        "vizwiz_train_annotations_json_path",
    ],
    "eval_textvqa": [
        "textvqa_image_dir_path",
        "textvqa_train_questions_json_path",
        "textvqa_train_annotations_json_path",
    ],
    "eval_imagenet": ["imagenet_root"],
    "eval_hateful_memes": [
        "hateful_memes_image_dir_path",
        "hateful_memes_train_annotations_json_path",
    ],
}


def add_arg(cmd: List[str], flag: str, value) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        if value:
            cmd.append(flag)
        return
    if isinstance(value, (list, tuple)):
        if not value:
            return
        cmd.append(flag)
        cmd.extend(str(item) for item in value)
        return
    cmd.extend([flag, str(value)])


def require_fields(args: argparse.Namespace, fields: Sequence[str], label: str) -> None:
    missing = [field for field in fields if getattr(args, field) in (None, False, [])]
    if missing:
        raise SystemExit(f"{label} requires: {', '.join('--' + m for m in missing)}")


def selected_dataset_flags(args: argparse.Namespace) -> List[str]:
    return [flag for flag in EVAL_DATASET_FLAGS if getattr(args, flag)]


def add_alias_arg(parser: argparse.ArgumentParser, name: str, **kwargs) -> None:
    """Add both source-style underscore and user-friendly hyphen spellings."""
    parser.add_argument(f"--{name}", f"--{name.replace('_', '-')}", dest=name, **kwargs)


def add_dataset_selectors(parser: argparse.ArgumentParser) -> None:
    for flag in EVAL_DATASET_FLAGS:
        add_alias_arg(parser, flag, action="store_true", default=False)


def add_caption_paths(parser: argparse.ArgumentParser) -> None:
    add_alias_arg(parser, "flickr_image_dir_path", default=None)
    add_alias_arg(parser, "flickr_karpathy_json_path", default=None)
    add_alias_arg(parser, "flickr_annotations_json_path", default=None)

    add_alias_arg(parser, "coco_train_image_dir_path", default=None)
    add_alias_arg(parser, "coco_val_image_dir_path", default=None)
    add_alias_arg(parser, "coco_karpathy_json_path", default=None)
    add_alias_arg(parser, "coco_annotations_json_path", default=None)


def add_vqa_paths(parser: argparse.ArgumentParser, include_eval_only_paths: bool) -> None:
    add_alias_arg(parser, "vqav2_train_image_dir_path", default=None)
    add_alias_arg(parser, "vqav2_train_questions_json_path", default=None)
    add_alias_arg(parser, "vqav2_train_annotations_json_path", default=None)
    add_alias_arg(parser, "vqav2_test_image_dir_path", default=None)
    add_alias_arg(parser, "vqav2_test_questions_json_path", default=None)
    if include_eval_only_paths:
        add_alias_arg(parser, "vqav2_test_annotations_json_path", default=None)
        add_alias_arg(parser, "vqav2_final_test_questions_json_path", default=None)

    add_alias_arg(parser, "ok_vqa_train_image_dir_path", default=None)
    add_alias_arg(parser, "ok_vqa_train_questions_json_path", default=None)
    add_alias_arg(parser, "ok_vqa_train_annotations_json_path", default=None)
    add_alias_arg(parser, "ok_vqa_test_image_dir_path", default=None)
    add_alias_arg(parser, "ok_vqa_test_questions_json_path", default=None)
    if include_eval_only_paths:
        add_alias_arg(parser, "ok_vqa_test_annotations_json_path", default=None)

    add_alias_arg(parser, "vizwiz_train_image_dir_path", default=None)
    add_alias_arg(parser, "vizwiz_train_questions_json_path", default=None)
    add_alias_arg(parser, "vizwiz_train_annotations_json_path", default=None)
    add_alias_arg(parser, "vizwiz_test_image_dir_path", default=None)
    add_alias_arg(parser, "vizwiz_test_questions_json_path", default=None)
    if include_eval_only_paths:
        add_alias_arg(parser, "vizwiz_test_annotations_json_path", default=None)

    add_alias_arg(parser, "textvqa_image_dir_path", default=None)
    add_alias_arg(parser, "textvqa_train_questions_json_path", default=None)
    add_alias_arg(parser, "textvqa_train_annotations_json_path", default=None)
    add_alias_arg(parser, "textvqa_test_questions_json_path", default=None)
    if include_eval_only_paths:
        add_alias_arg(parser, "textvqa_test_annotations_json_path", default=None)


def add_classification_paths(parser: argparse.ArgumentParser, include_eval_only_paths: bool) -> None:
    add_alias_arg(parser, "imagenet_root", default=None)
    add_alias_arg(parser, "hateful_memes_image_dir_path", default=None)
    add_alias_arg(parser, "hateful_memes_train_annotations_json_path", default=None)
    if include_eval_only_paths:
        add_alias_arg(parser, "hateful_memes_test_annotations_json_path", default=None)


def add_evaluate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("evaluate", help="Build an evaluate.py command")
    parser.add_argument("--model", default="open_flamingo")
    add_alias_arg(parser, "results_file", default=None)
    parser.add_argument("--shots", nargs="+", type=int, default=[0, 4, 8, 16, 32])
    add_alias_arg(parser, "num_trials", type=int, default=1)
    add_alias_arg(parser, "trial_seeds", nargs="+", type=int, default=[42])
    add_alias_arg(parser, "num_samples", type=int, default=-1)
    add_alias_arg(parser, "query_set_size", type=int, default=2048)
    add_alias_arg(parser, "batch_size", type=int, default=8)
    add_alias_arg(
        parser,
        "no_caching_for_classification",
        action="store_true",
        default=False,
    )
    add_alias_arg(
        parser,
        "classification_prompt_ensembling",
        action="store_true",
        default=False,
    )
    parser.add_argument("--rices", action="store_true", default=False)
    add_alias_arg(parser, "rices_vision_encoder_path", default="ViT-L-14")
    add_alias_arg(parser, "rices_vision_encoder_pretrained", default="openai")
    add_alias_arg(parser, "cached_demonstration_features", default=None)

    add_alias_arg(parser, "vision_encoder_path", default=None)
    add_alias_arg(parser, "vision_encoder_pretrained", default=None)
    add_alias_arg(parser, "lm_path", default=None)
    add_alias_arg(parser, "lm_tokenizer_path", default=None)
    add_alias_arg(parser, "checkpoint_path", default=None)
    add_alias_arg(parser, "cross_attn_every_n_layers", default=None)
    parser.add_argument("--precision", default=None)

    add_dataset_selectors(parser)
    add_caption_paths(parser)
    add_vqa_paths(parser, include_eval_only_paths=True)
    add_classification_paths(parser, include_eval_only_paths=True)

    parser.add_argument("--dist-url", default="env://")
    parser.add_argument("--dist-backend", default="nccl")
    parser.add_argument("--horovod", action="store_true", default=False)
    parser.add_argument("--no-set-device-rank", action="store_true", default=False)


def add_cache_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("cache-rices", help="Build a cache_rices_features.py command")
    add_alias_arg(parser, "output_dir", default=None)
    add_alias_arg(parser, "vision_encoder_path", default="ViT-L-14")
    add_alias_arg(parser, "vision_encoder_pretrained", default="openai")
    add_alias_arg(parser, "batch_size", type=int, default=256)

    add_dataset_selectors(parser)
    add_caption_paths(parser)
    add_vqa_paths(parser, include_eval_only_paths=False)
    add_classification_paths(parser, include_eval_only_paths=False)


def validate_evaluate(args: argparse.Namespace) -> None:
    selected = selected_dataset_flags(args)
    if not selected:
        raise SystemExit("Select at least one dataset flag such as --eval_coco or --eval_vqav2")

    require_fields(
        args,
        [
            "vision_encoder_path",
            "vision_encoder_pretrained",
            "lm_path",
            "lm_tokenizer_path",
            "checkpoint_path",
            "cross_attn_every_n_layers",
            "precision",
        ],
        "evaluate mode",
    )

    for flag in selected:
        require_fields(args, EVAL_REQUIRED[flag], flag)
        if flag == "eval_vqav2":
            if getattr(args, "vqav2_test_annotations_json_path") is None and getattr(
                args, "vqav2_final_test_questions_json_path"
            ) is None:
                raise SystemExit(
                    "eval_vqav2 needs either --vqav2_test_annotations_json_path or --vqav2_final_test_questions_json_path"
                )


def validate_cache(args: argparse.Namespace) -> None:
    selected = selected_dataset_flags(args)
    if not selected:
        raise SystemExit("Select at least one dataset flag such as --eval_coco or --eval_vqav2")

    require_fields(
        args,
        ["output_dir", "vision_encoder_path", "vision_encoder_pretrained"],
        "cache-rices mode",
    )

    if "eval_imagenet" in selected:
        raise SystemExit(
            "cache-rices mode cannot render ImageNet caching: the source cache script "
            "parses ImageNet flags but does not save imagenet.pkl"
        )

    for flag in selected:
        require_fields(args, CACHE_REQUIRED[flag], flag)


def build_evaluate_command(args: argparse.Namespace) -> str:
    validate_evaluate(args)
    wrapper = str(Path(__file__).resolve().with_name("run_evaluation_entrypoint.py"))
    cmd = ["python", wrapper]

    for flag in [
        "model",
        "results_file",
        "shots",
        "num_trials",
        "trial_seeds",
        "num_samples",
        "query_set_size",
        "batch_size",
        "no_caching_for_classification",
        "classification_prompt_ensembling",
        "rices",
        "rices_vision_encoder_path",
        "rices_vision_encoder_pretrained",
        "cached_demonstration_features",
        "vision_encoder_path",
        "vision_encoder_pretrained",
        "lm_path",
        "lm_tokenizer_path",
        "checkpoint_path",
        "cross_attn_every_n_layers",
        "precision",
    ]:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    for flag in EVAL_DATASET_FLAGS:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    for flag in [
        "flickr_image_dir_path",
        "flickr_karpathy_json_path",
        "flickr_annotations_json_path",
        "coco_train_image_dir_path",
        "coco_val_image_dir_path",
        "coco_karpathy_json_path",
        "coco_annotations_json_path",
        "vqav2_train_image_dir_path",
        "vqav2_train_questions_json_path",
        "vqav2_train_annotations_json_path",
        "vqav2_test_image_dir_path",
        "vqav2_test_questions_json_path",
        "vqav2_test_annotations_json_path",
        "vqav2_final_test_questions_json_path",
        "ok_vqa_train_image_dir_path",
        "ok_vqa_train_questions_json_path",
        "ok_vqa_train_annotations_json_path",
        "ok_vqa_test_image_dir_path",
        "ok_vqa_test_questions_json_path",
        "ok_vqa_test_annotations_json_path",
        "vizwiz_train_image_dir_path",
        "vizwiz_train_questions_json_path",
        "vizwiz_train_annotations_json_path",
        "vizwiz_test_image_dir_path",
        "vizwiz_test_questions_json_path",
        "vizwiz_test_annotations_json_path",
        "textvqa_image_dir_path",
        "textvqa_train_questions_json_path",
        "textvqa_train_annotations_json_path",
        "textvqa_test_questions_json_path",
        "textvqa_test_annotations_json_path",
        "imagenet_root",
        "hateful_memes_image_dir_path",
        "hateful_memes_train_annotations_json_path",
        "hateful_memes_test_annotations_json_path",
    ]:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    for flag in ["dist_url", "dist_backend", "horovod", "no_set_device_rank"]:
        add_arg(cmd, f"--{flag.replace('_', '-')}", getattr(args, flag))

    return shlex.join(cmd)


def build_cache_command(args: argparse.Namespace) -> str:
    validate_cache(args)
    wrapper = str(Path(__file__).resolve().with_name("run_cache_rices_entrypoint.py"))
    cmd = ["python", wrapper]

    for flag in ["output_dir", "vision_encoder_path", "vision_encoder_pretrained", "batch_size"]:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    for flag in EVAL_DATASET_FLAGS:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    for flag in [
        "flickr_image_dir_path",
        "flickr_karpathy_json_path",
        "flickr_annotations_json_path",
        "coco_train_image_dir_path",
        "coco_val_image_dir_path",
        "coco_karpathy_json_path",
        "coco_annotations_json_path",
        "vqav2_train_image_dir_path",
        "vqav2_train_questions_json_path",
        "vqav2_train_annotations_json_path",
        "ok_vqa_train_image_dir_path",
        "ok_vqa_train_questions_json_path",
        "ok_vqa_train_annotations_json_path",
        "vizwiz_train_image_dir_path",
        "vizwiz_train_questions_json_path",
        "vizwiz_train_annotations_json_path",
        "textvqa_image_dir_path",
        "textvqa_train_questions_json_path",
        "textvqa_train_annotations_json_path",
        "imagenet_root",
        "hateful_memes_image_dir_path",
        "hateful_memes_train_annotations_json_path",
    ]:
        add_arg(cmd, f"--{flag}", getattr(args, flag))

    return shlex.join(cmd)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    add_evaluate_parser(subparsers)
    add_cache_parser(subparsers)
    args = parser.parse_args(argv)

    if args.mode == "evaluate":
        print(build_evaluate_command(args))
    else:
        print(build_cache_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

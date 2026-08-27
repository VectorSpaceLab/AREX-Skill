#!/usr/bin/env python3
"""Render Graphormer pretrained-evaluation or MolHIV fine-tuning commands.

This helper never runs training or evaluation. It only prints a command plan
that a user can review and execute separately.
"""

from __future__ import annotations

import argparse
import shlex
from typing import List, Sequence

PRETRAINED_MODELS = {
    "pcqm4mv1_graphormer_base": {
        "purpose": "PCQM4M v1 pretrained Graphormer base checkpoint",
        "dataset_name": "pcqm4m",
        "dataset_source": "ogb",
        "task": "graph_prediction",
        "criterion": "l1_loss",
        "arch": "graphormer_base",
        "num_classes": 1,
        "eval_supported": True,
    },
    "pcqm4mv2_graphormer_base": {
        "purpose": "PCQM4M v2 pretrained Graphormer base checkpoint",
        "dataset_name": "pcqm4mv2",
        "dataset_source": "ogb",
        "task": "graph_prediction",
        "criterion": "l1_loss",
        "arch": "graphormer_base",
        "num_classes": 1,
        "eval_supported": True,
    },
    "pcqm4mv1_graphormer_base_for_molhiv": {
        "purpose": "MolHIV-oriented checkpoint used by the FLAG fine-tuning recipe",
        "dataset_name": "ogbg-molhiv",
        "dataset_source": "ogb",
        "task": "graph_prediction_with_flag",
        "criterion": "binary_logloss_with_flag",
        "arch": "graphormer_base",
        "num_classes": 1,
        "eval_supported": False,
    },
    "oc20is2re_graphormer3d_base": {
        "purpose": "Graphormer3D IS2RE checkpoint for OC20",
        "dataset_name": "is2re",
        "dataset_source": "unknown",
        "task": "is2re",
        "criterion": "mae_deltapos",
        "arch": "graphormer3d_base",
        "num_classes": 1,
        "eval_supported": False,
        "note": "source marks the checkpoint URL as temporarily unavailable",
    },
}


def quote_command(parts: Sequence[str], gpu_ids: str | None) -> str:
    rendered = " \\\n  ".join(shlex.quote(str(part)) for part in parts)
    if gpu_ids:
        return f"CUDA_VISIBLE_DEVICES={shlex.quote(gpu_ids)} {rendered}"
    return rendered


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render Graphormer pretrained evaluation or MolHIV fine-tuning commands "
            "without executing them."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=("evaluate-pretrained", "evaluate-checkpoints", "finetune-molhiv"),
        help="Command family to render.",
    )
    parser.add_argument(
        "--user-dir",
        default="graphormer",
        help="Graphormer fairseq user-dir path used in the rendered command.",
    )
    parser.add_argument(
        "--save-dir",
        default="ckpts",
        help="Checkpoint directory used for checkpoint evaluation or fine-tuning output.",
    )
    parser.add_argument(
        "--split",
        default=None,
        help="Dataset split to evaluate; defaults depend on the selected mode.",
    )
    parser.add_argument(
        "--metric",
        choices=("auc", "mae"),
        default=None,
        help="Metric to use for checkpoint evaluation.",
    )
    parser.add_argument(
        "--pretrained-model-name",
        default="auto",
        choices=("auto", *PRETRAINED_MODELS.keys()),
        help="Pretrained checkpoint name.",
    )
    parser.add_argument(
        "--load-output-layer",
        action="store_true",
        default=None,
        help="Keep the pretrained output layer instead of resetting it.",
    )
    parser.add_argument(
        "--no-load-output-layer",
        action="store_true",
        default=None,
        help="Force the rendered command to omit the pretrained output layer.",
    )
    parser.add_argument(
        "--gpu-ids",
        default=None,
        help="Optional CUDA_VISIBLE_DEVICES value to prefix onto the command.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable token used in the rendered command.",
    )
    parser.add_argument(
        "--evaluate-script",
        default="graphormer/evaluate/evaluate.py",
        help="Path to the evaluation entry point inside the checkout.",
    )
    parser.add_argument(
        "--fairseq-train",
        default="fairseq-train",
        help="Training entry point token used in the rendered fine-tuning command.",
    )
    parser.add_argument(
        "--dataset-name",
        default=None,
        help="Override the rendered dataset name.",
    )
    parser.add_argument(
        "--dataset-source",
        default=None,
        help="Override the rendered dataset source.",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="Override the rendered Graphormer task.",
    )
    parser.add_argument(
        "--criterion",
        default=None,
        help="Override the rendered criterion.",
    )
    parser.add_argument(
        "--arch",
        default=None,
        help="Override the rendered architecture.",
    )
    parser.add_argument(
        "--num-classes",
        type=positive_int,
        default=None,
        help="Override the rendered num-classes value.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=None,
        help="Override the rendered batch size.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=16,
        help="Data-loader worker count used in the rendered command.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Random seed used in the rendered command.",
    )
    parser.add_argument(
        "--pre-layernorm",
        action="store_true",
        default=None,
        help="Force the rendered command to include --pre-layernorm.",
    )
    parser.add_argument(
        "--no-pre-layernorm",
        action="store_true",
        default=None,
        help="Force the rendered command to omit --pre-layernorm.",
    )
    parser.add_argument(
        "--epoch",
        type=positive_int,
        default=4,
        help="Source recipe epoch hint used for MolHIV fine-tuning.",
    )
    parser.add_argument(
        "--max-epoch",
        type=positive_int,
        default=None,
        help="Override the fine-tuning max-epoch.",
    )
    parser.add_argument(
        "--total-num-update",
        type=positive_int,
        default=None,
        help="Override the fine-tuning total-number-of-updates value.",
    )
    parser.add_argument(
        "--warmup-updates",
        type=positive_int,
        default=None,
        help="Override the fine-tuning warmup-updates value.",
    )
    parser.add_argument(
        "--flag-m",
        type=positive_int,
        default=3,
        help="FLAG perturbation count used by MolHIV fine-tuning.",
    )
    parser.add_argument(
        "--flag-step-size",
        type=float,
        default=0.01,
        help="FLAG step size used by MolHIV fine-tuning.",
    )
    parser.add_argument(
        "--flag-mag",
        type=float,
        default=0.0,
        help="FLAG magnitude used by MolHIV fine-tuning.",
    )
    return parser


def resolve_pretrained_name(mode: str, requested: str) -> str:
    if requested != "auto":
        return requested
    if mode == "finetune-molhiv":
        return "pcqm4mv1_graphormer_base_for_molhiv"
    return "pcqm4mv1_graphormer_base"


def resolve_choice(value: str | None, default: str) -> str:
    return default if value in (None, "") else value


def decide_output_layer(args: argparse.Namespace, default: bool) -> bool:
    if args.load_output_layer and args.no_load_output_layer:
        raise SystemExit("Choose only one of --load-output-layer or --no-load-output-layer.")
    if args.load_output_layer:
        return True
    if args.no_load_output_layer:
        return False
    return default


def decide_pre_layernorm(args: argparse.Namespace, default: bool) -> bool:
    if args.pre_layernorm and args.no_pre_layernorm:
        raise SystemExit("Choose only one of --pre-layernorm or --no-pre-layernorm.")
    if args.pre_layernorm:
        return True
    if args.no_pre_layernorm:
        return False
    return default


def render_evaluate_pretrained(args: argparse.Namespace, pretrained_name: str) -> tuple[str, List[str]]:
    meta = PRETRAINED_MODELS[pretrained_name]
    if not meta["eval_supported"]:
        raise SystemExit(
            f"{pretrained_name} is not a supported evaluate-pretrained target in the source recipe."
        )

    dataset_name = resolve_choice(args.dataset_name, meta["dataset_name"])
    dataset_source = resolve_choice(args.dataset_source, meta["dataset_source"])
    task = resolve_choice(args.task, meta["task"])
    criterion = resolve_choice(args.criterion, meta["criterion"])
    arch = resolve_choice(args.arch, meta["arch"])
    num_classes = args.num_classes if args.num_classes is not None else meta["num_classes"]
    batch_size = args.batch_size if args.batch_size is not None else 64
    split = resolve_choice(args.split, "valid")
    load_output = decide_output_layer(args, default=True)
    pre_layernorm = decide_pre_layernorm(args, default=False)

    parts = [
        args.python,
        args.evaluate_script,
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        dataset_name,
        "--dataset-source",
        dataset_source,
        "--task",
        task,
        "--criterion",
        criterion,
        "--arch",
        arch,
        "--num-classes",
        str(num_classes),
        "--batch-size",
        str(batch_size),
        "--pretrained-model-name",
        pretrained_name,
    ]
    if load_output:
        parts.append("--load-pretrained-model-output-layer")
    parts += ["--split", split, "--seed", str(args.seed)]
    if pre_layernorm:
        parts.append("--pre-layernorm")

    notes = [
        "The evaluation script strict-loads the checkpoint into the constructed model.",
        "The script moves model and samples to CUDA; it is not CPU-safe as written.",
    ]
    if not load_output:
        notes.append(
            "The pretrained output layer is omitted, so the rendered command is for transfer rather than same-head evaluation."
        )
    if args.save_dir and args.save_dir != "ckpts":
        notes.append(f"The save-dir flag is accepted but unused in pretrained evaluation: {args.save_dir}")
    return quote_command(parts, args.gpu_ids), notes


def render_evaluate_checkpoints(args: argparse.Namespace, pretrained_name: str) -> tuple[str, List[str]]:
    metric = resolve_choice(args.metric, "auc")
    dataset_name = resolve_choice(
        args.dataset_name,
        "ogbg-molhiv" if metric == "auc" else "pcqm4m",
    )
    dataset_source = resolve_choice(args.dataset_source, "ogb")
    task = resolve_choice(args.task, "graph_prediction")
    criterion = resolve_choice(
        args.criterion,
        "binary_logloss" if metric == "auc" else "l1_loss",
    )
    arch = resolve_choice(args.arch, "graphormer_base")
    num_classes = args.num_classes if args.num_classes is not None else 1
    batch_size = args.batch_size if args.batch_size is not None else 64
    split = resolve_choice(
        args.split,
        "test" if metric == "auc" else "valid",
    )
    if args.load_output_layer and args.no_load_output_layer:
        raise SystemExit("Choose only one of --load-output-layer or --no-load-output-layer.")
    pre_layernorm = decide_pre_layernorm(args, default=(metric == "auc"))

    parts = [
        args.python,
        args.evaluate_script,
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        dataset_name,
        "--dataset-source",
        dataset_source,
        "--task",
        task,
        "--criterion",
        criterion,
        "--arch",
        arch,
        "--num-classes",
        str(num_classes),
        "--batch-size",
        str(batch_size),
        "--save-dir",
        args.save_dir,
        "--split",
        split,
        "--metric",
        metric,
        "--seed",
        str(args.seed),
    ]
    parts += ["--pretrained-model-name", "none"]
    if pre_layernorm:
        parts.append("--pre-layernorm")

    notes = [
        "The evaluation script walks every entry in the save-dir directory, so keep it checkpoint-only.",
        "Checkpoint-directory evaluation forces --pretrained-model-name none so evaluate.py uses the save-dir loop.",
        "Use AUC for binary classification checkpoints and MAE for regression checkpoints.",
        "The metric branch does not apply to the built-in pretrained PCQM4M evaluator path.",
    ]
    if args.pretrained_model_name != "auto":
        notes.append("The provided pretrained-model-name is accepted for CLI consistency but ignored in checkpoint mode.")
    if args.load_output_layer or args.no_load_output_layer:
        notes.append("Output-layer flags are ignored in checkpoint mode because no pretrained state is loaded.")
    if args.save_dir == "ckpts":
        notes.append("The default save-dir is fine for rendering, but the directory should exist before execution.")
    return quote_command(parts, args.gpu_ids), notes


def render_finetune_molhiv(args: argparse.Namespace, pretrained_name: str) -> tuple[str, List[str]]:
    if pretrained_name == "oc20is2re_graphormer3d_base":
        raise SystemExit("The OC20 checkpoint is not part of the MolHIV fine-tune recipe.")

    batch_size = args.batch_size if args.batch_size is not None else 128
    n_gpu = 1
    if args.gpu_ids:
        n_gpu = len([piece for piece in args.gpu_ids.split(",") if piece.strip()]) or 1
    total_updates = args.total_num_update if args.total_num_update is not None else max(
        1, (33000 * args.epoch) // (batch_size * n_gpu)
    )
    warmup_updates = args.warmup_updates if args.warmup_updates is not None else max(
        1, (total_updates * 16) // 100
    )
    max_epoch = args.max_epoch if args.max_epoch is not None else args.epoch + 1
    load_output = decide_output_layer(args, default=False)
    pre_layernorm = decide_pre_layernorm(args, default=True)
    task = resolve_choice(args.task, "graph_prediction_with_flag")
    criterion = resolve_choice(args.criterion, "binary_logloss_with_flag")
    arch = resolve_choice(args.arch, "graphormer_base")
    dataset_name = resolve_choice(args.dataset_name, "ogbg-molhiv")
    dataset_source = resolve_choice(args.dataset_source, "ogb")
    num_classes = args.num_classes if args.num_classes is not None else 1

    parts = [
        args.fairseq_train,
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        dataset_name,
        "--dataset-source",
        dataset_source,
        "--task",
        task,
        "--criterion",
        criterion,
        "--arch",
        arch,
        "--num-classes",
        str(num_classes),
        "--attention-dropout",
        "0.1",
        "--act-dropout",
        "0.1",
        "--dropout",
        "0.0",
        "--optimizer",
        "adam",
        "--adam-betas",
        "(0.9, 0.999)",
        "--adam-eps",
        "1e-8",
        "--clip-norm",
        "5.0",
        "--weight-decay",
        "0.0",
        "--lr-scheduler",
        "polynomial_decay",
        "--power",
        "1",
        "--warmup-updates",
        str(warmup_updates),
        "--total-num-update",
        str(total_updates),
        "--lr",
        "2e-4",
        "--end-learning-rate",
        "1e-5",
        "--batch-size",
        str(batch_size),
        "--fp16",
        "--data-buffer-size",
        "20",
        "--encoder-layers",
        "12",
        "--encoder-embed-dim",
        "768",
        "--encoder-ffn-embed-dim",
        "768",
        "--encoder-attention-heads",
        "32",
        "--max-epoch",
        str(max_epoch),
        "--save-dir",
        args.save_dir,
        "--pretrained-model-name",
        pretrained_name,
        "--seed",
        str(args.seed),
        "--flag-m",
        str(args.flag_m),
        "--flag-step-size",
        str(args.flag_step_size),
        "--flag-mag",
        str(args.flag_mag),
    ]
    if load_output:
        parts.append("--load-pretrained-model-output-layer")
    if pre_layernorm:
        parts.append("--pre-layernorm")

    notes = [
        "The rendered recipe mirrors the maintained MolHIV FLAG example and stays command-only.",
        "The pretrained checkpoint name should usually be the MolHIV-oriented checkpoint for this workflow.",
        "This command expects CUDA and the OGB MolHIV dataset at execution time.",
    ]
    if not load_output:
        notes.append("The output layer will be reset after loading the checkpoint, which is the usual fine-tuning choice.")
    return quote_command(parts, args.gpu_ids), notes


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    pretrained_name = resolve_pretrained_name(args.mode, args.pretrained_model_name)
    if args.mode == "evaluate-pretrained":
        command, notes = render_evaluate_pretrained(args, pretrained_name)
    elif args.mode == "evaluate-checkpoints":
        command, notes = render_evaluate_checkpoints(args, pretrained_name)
    elif args.mode == "finetune-molhiv":
        command, notes = render_finetune_molhiv(args, pretrained_name)
    else:  # pragma: no cover - guarded by argparse choices
        raise SystemExit(f"Unsupported mode: {args.mode}")

    print("# Rendered command only; nothing was executed.")
    for note in notes:
        print(f"# {note}")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

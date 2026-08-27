#!/usr/bin/env python3
"""Render safe Graphormer fairseq training commands.

The script only prints a command and a few notes. It never launches training,
downloads data, or touches checkpoints.
"""

from __future__ import annotations

import argparse
import math
import shlex
from typing import List, Sequence, Tuple


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
            "Render a Graphormer fairseq training command for common property, "
            "FLAG, and OC20/IS2RE workflows without executing it."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=("zinc", "pcqm4m-v1", "pcqm4mv2", "molhiv-flag", "oc20-is2re"),
        help="Training workflow to render.",
    )
    parser.add_argument(
        "--user-dir",
        default="graphormer",
        help="Graphormer fairseq user-dir path used in the rendered command.",
    )
    parser.add_argument(
        "--gpu-ids",
        default=None,
        help="Optional CUDA_VISIBLE_DEVICES value to prefix onto the command.",
    )
    parser.add_argument(
        "--save-dir",
        default="./ckpts",
        help="Checkpoint output directory.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=16,
        help="Data-loader worker count used in the rendered command.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=None,
        help="Override the recipe batch size when the selected workflow supports it.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Random seed used in the rendered command.",
    )
    parser.add_argument(
        "--pretrained-model-name",
        default="pcqm4mv1_graphormer_base_for_molhiv",
        help="Pretrained model name used by the MolHIV FLAG recipe.",
    )
    parser.add_argument(
        "--load-output-layer",
        action="store_true",
        help="Keep the pretrained output layer when rendering MolHIV fine-tuning.",
    )
    parser.add_argument(
        "--no-load-output-layer",
        action="store_true",
        help="Force the rendered MolHIV command to omit the pretrained output layer.",
    )
    parser.add_argument(
        "--pre-layernorm",
        action="store_true",
        help="Force `--pre-layernorm` on the rendered command.",
    )
    parser.add_argument(
        "--no-pre-layernorm",
        action="store_true",
        help="Force omission of `--pre-layernorm` on the rendered command.",
    )
    parser.add_argument(
        "--epoch",
        type=positive_int,
        default=4,
        help="Source recipe epoch hint used by the MolHIV FLAG formula.",
    )
    parser.add_argument(
        "--max-epoch",
        type=positive_int,
        default=None,
        help="Override the MolHIV max-epoch.",
    )
    parser.add_argument(
        "--total-num-update",
        type=positive_int,
        default=None,
        help="Override the MolHIV total-num-update value.",
    )
    parser.add_argument(
        "--warmup-updates",
        type=positive_int,
        default=None,
        help="Override the MolHIV warmup-updates value.",
    )
    parser.add_argument(
        "--data-path",
        default="./data/is2re_train_val_test_lmdbs/data/is2re/all",
        help="OC20/IS2RE data path used as the positional argument.",
    )
    return parser


def render_common_prefix(gpu_ids: str | None) -> str:
    if gpu_ids:
        return f"CUDA_VISIBLE_DEVICES={shlex.quote(gpu_ids)} "
    return ""


def render_zinc(args: argparse.Namespace) -> Tuple[str, List[str]]:
    batch_size = args.batch_size if args.batch_size is not None else 64
    parts = [
        "fairseq-train",
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        "zinc",
        "--dataset-source",
        "pyg",
        "--task",
        "graph_prediction",
        "--criterion",
        "l1_loss",
        "--arch",
        "graphormer_slim",
        "--num-classes",
        "1",
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
        "0.01",
        "--lr-scheduler",
        "polynomial_decay",
        "--power",
        "1",
        "--warmup-updates",
        "60000",
        "--total-num-update",
        "400000",
        "--lr",
        "2e-4",
        "--end-learning-rate",
        "1e-9",
        "--batch-size",
        str(batch_size),
        "--fp16",
        "--data-buffer-size",
        "20",
        "--encoder-layers",
        "12",
        "--encoder-embed-dim",
        "80",
        "--encoder-ffn-embed-dim",
        "80",
        "--encoder-attention-heads",
        "8",
        "--max-epoch",
        "10000",
        "--save-dir",
        args.save_dir,
    ]
    notes = [
        "ZINC uses the PyG source path and a scalar regression head.",
        "The historical recipe assumes a CUDA-capable GPU and fp16.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_pcqm4m_v1(args: argparse.Namespace) -> Tuple[str, List[str]]:
    batch_size = args.batch_size if args.batch_size is not None else 64
    parts = [
        "fairseq-train",
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        "pcqm4m",
        "--dataset-source",
        "ogb",
        "--task",
        "graph_prediction",
        "--criterion",
        "l1_loss",
        "--arch",
        "graphormer_base",
        "--num-classes",
        "1",
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
        "60000",
        "--total-num-update",
        "1000000",
        "--lr",
        "2e-4",
        "--end-learning-rate",
        "1e-9",
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
        "300",
        "--save-dir",
        args.save_dir,
    ]
    notes = [
        "PCQM4M v1 uses the OGB source path and a graph regression head.",
        "The recipe matches the historical Graphormer base configuration.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_pcqm4mv2(args: argparse.Namespace) -> Tuple[str, List[str]]:
    batch_size = args.batch_size if args.batch_size is not None else 256
    parts = [
        "fairseq-train",
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        "pcqm4mv2",
        "--dataset-source",
        "ogb",
        "--task",
        "graph_prediction",
        "--criterion",
        "l1_loss",
        "--arch",
        "graphormer_base",
        "--num-classes",
        "1",
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
        "60000",
        "--total-num-update",
        "1000000",
        "--lr",
        "2e-4",
        "--end-learning-rate",
        "1e-9",
        "--batch-size",
        str(batch_size),
        "--fp16",
        "--data-buffer-size",
        "20",
        "--save-dir",
        args.save_dir,
    ]
    notes = [
        "PCQM4Mv2 uses the OGB LSC source path and a larger batch size in the historical recipe.",
        "The recipe still assumes a CUDA-capable GPU for fp16 training.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_molhiv_flag(args: argparse.Namespace) -> Tuple[str, List[str]]:
    batch_size = args.batch_size if args.batch_size is not None else 128
    if args.load_output_layer and args.no_load_output_layer:
        raise SystemExit("Choose only one of --load-output-layer or --no-load-output-layer.")
    if args.pre_layernorm and args.no_pre_layernorm:
        raise SystemExit("Choose only one of --pre-layernorm or --no-pre-layernorm.")
    load_output = args.load_output_layer
    if args.no_load_output_layer:
        load_output = False
    pre_layernorm = True if not args.no_pre_layernorm else False
    if args.pre_layernorm:
        pre_layernorm = True
    total_updates = args.total_num_update if args.total_num_update is not None else max(
        1, (33000 * args.epoch) // batch_size
    )
    warmup_updates = args.warmup_updates if args.warmup_updates is not None else max(
        1, (total_updates * 16) // 100
    )
    max_epoch = args.max_epoch if args.max_epoch is not None else args.epoch + 1

    parts = [
        "fairseq-train",
        "--user-dir",
        args.user_dir,
        "--num-workers",
        str(args.num_workers),
        "--ddp-backend=legacy_ddp",
        "--dataset-name",
        "ogbg-molhiv",
        "--dataset-source",
        "ogb",
        "--task",
        "graph_prediction_with_flag",
        "--criterion",
        "binary_logloss_with_flag",
        "--arch",
        "graphormer_base",
        "--num-classes",
        "1",
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
        args.pretrained_model_name,
        "--seed",
        str(args.seed),
        "--flag-m",
        "3",
        "--flag-step-size",
        "0.01",
        "--flag-mag",
        "0",
    ]
    if load_output:
        parts.append("--load-pretrained-model-output-layer")
    if pre_layernorm:
        parts.append("--pre-layernorm")
    notes = [
        "This is the FLAG fine-tuning recipe used for MolHIV-style training.",
        "The recipe expects a CUDA-capable GPU and an OGB dataset download.",
        "The pretrained checkpoint family is part of the fine-tuning workflow.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def render_oc20_is2re(args: argparse.Namespace) -> Tuple[str, List[str]]:
    batch_size = args.batch_size if args.batch_size is not None else 4
    parts = [
        "fairseq-train",
        "--user-dir",
        args.user_dir,
        args.data_path,
        "--valid-subset",
        "val_id,val_ood_ads,val_ood_cat,val_ood_both",
        "--best-checkpoint-metric",
        "loss",
        "--num-workers",
        "0",
        "--ddp-backend=c10d",
        "--task",
        "is2re",
        "--criterion",
        "mae_deltapos",
        "--arch",
        "graphormer3d_base",
        "--optimizer",
        "adam",
        "--adam-betas",
        "(0.9, 0.98)",
        "--adam-eps",
        "1e-6",
        "--clip-norm",
        "5.0",
        "--lr-scheduler",
        "polynomial_decay",
        "--lr",
        "3e-4",
        "--warmup-updates",
        "10000",
        "--total-num-update",
        "1000000",
        "--batch-size",
        str(batch_size),
        "--dropout",
        "0.0",
        "--attention-dropout",
        "0.1",
        "--weight-decay",
        "0.001",
        "--update-freq",
        "1",
        "--seed",
        str(args.seed),
        "--fp16",
        "--fp16-init-scale",
        "4",
        "--fp16-scale-window",
        "256",
        "--tensorboard-logdir",
        "./tsbs",
        "--embed-dim",
        "768",
        "--ffn-embed-dim",
        "768",
        "--attention-heads",
        "48",
        "--max-update",
        "1000000",
        "--log-interval",
        "100",
        "--log-format",
        "simple",
        "--save-interval-updates",
        "5000",
        "--validate-interval-updates",
        "2500",
        "--keep-interval-updates",
        "30",
        "--no-epoch-checkpoints",
        "--save-dir",
        args.save_dir,
        "--layers",
        "12",
        "--blocks",
        "4",
        "--required-batch-size-multiple",
        "1",
        "--node-loss-weight",
        "15",
    ]
    notes = [
        "The OC20/IS2RE recipe is the heaviest command in the core training family.",
        "The historical notes warn that batch size 4 requires at least 32 GB of GPU memory.",
        "The positional data path must point at the LMDB layout expected by the task.",
    ]
    return quote_command(parts, args.gpu_ids), notes


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    renderers = {
        "zinc": render_zinc,
        "pcqm4m-v1": render_pcqm4m_v1,
        "pcqm4mv2": render_pcqm4mv2,
        "molhiv-flag": render_molhiv_flag,
        "oc20-is2re": render_oc20_is2re,
    }
    command, notes = renderers[args.workflow](args)

    print("# Rendered command only; nothing was executed.")
    for note in notes:
        print(f"# {note}")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

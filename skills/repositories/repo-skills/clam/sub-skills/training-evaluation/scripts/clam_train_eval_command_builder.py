#!/usr/bin/env python3
"""Build safe CLAM training or evaluation commands.

This helper performs lightweight consistency checks and prints CLAM CLI commands.
It never imports CLAM, loads checkpoints, reads feature tensors, or launches
training/evaluation.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path


TASK_CLASS_HINTS = {
    "task_1_tumor_vs_normal": 2,
    "task_2_tumor_subtyping": 3,
}

ENCODER_DIMS = {
    "resnet50_trunc": 1024,
    "uni_v1": 1024,
    "conch_v1": 512,
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def fraction(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return parsed


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task", required=True, help="CLAM task name")
    parser.add_argument(
        "--model-type", choices=("clam_sb", "clam_mb", "mil"), default="clam_sb"
    )
    parser.add_argument("--model-size", choices=("small", "big"), default="small")
    parser.add_argument("--drop-out", type=float, default=0.25)
    parser.add_argument("--embed-dim", type=positive_int, default=None)
    parser.add_argument(
        "--encoder",
        choices=tuple(ENCODER_DIMS),
        default=None,
        help="optional upstream encoder hint used to check --embed-dim",
    )
    parser.add_argument(
        "--n-classes",
        type=positive_int,
        default=None,
        help="class count for custom tasks; known bundled tasks are inferred",
    )
    parser.add_argument(
        "--cuda-visible-devices",
        default=None,
        help="optional CUDA_VISIBLE_DEVICES value to prefix the command",
    )
    parser.add_argument(
        "--output-mode",
        choices=("command", "json"),
        default="command",
        help="print shell command or JSON summary",
    )


def infer_n_classes(task: str, provided: int | None) -> int | None:
    hinted = TASK_CLASS_HINTS.get(task)
    if provided is not None and hinted is not None and provided != hinted:
        raise ValueError(f"task {task} is known to use {hinted} classes, not {provided}")
    return provided if provided is not None else hinted


def resolve_embed_dim(embed_dim: int | None, encoder: str | None) -> tuple[int, list[str]]:
    warnings: list[str] = []
    if embed_dim is None and encoder is None:
        return 1024, ["defaulting --embed_dim to 1024; pass --encoder or --embed-dim to be explicit"]
    if embed_dim is None and encoder is not None:
        return ENCODER_DIMS[encoder], []
    if embed_dim is not None and encoder is not None and embed_dim != ENCODER_DIMS[encoder]:
        warnings.append(
            f"encoder {encoder} usually produces {ENCODER_DIMS[encoder]}-dim features, but --embed_dim is {embed_dim}"
        )
    return int(embed_dim), warnings


def validate_model_task(
    mode: str,
    task: str,
    model_type: str,
    n_classes: int | None,
    subtyping: bool,
) -> list[str]:
    warnings: list[str] = []
    if n_classes is None:
        warnings.append(
            "class count is unknown for this custom task; ensure script branches set args.n_classes correctly"
        )
    elif model_type == "mil" and n_classes == 2:
        warnings.append("binary MIL uses MIL_fc; multiclass MIL uses MIL_fc_mc")
    elif model_type == "mil" and n_classes > 2:
        warnings.append("multiclass MIL uses MIL_fc_mc and requires n_classes > 2")
    if mode == "train" and model_type in {"clam_sb", "clam_mb"} and n_classes and n_classes > 2 and not subtyping:
        raise ValueError("multiclass CLAM training should include --subtyping")
    if task not in TASK_CLASS_HINTS:
        warnings.append(
            "custom tasks require matching branches in create_splits_seq.py, main.py, and eval.py"
        )
    return warnings


def maybe_check_dir(path: str | None, label: str, warnings: list[str]) -> None:
    if not path:
        return
    candidate = Path(path)
    if candidate.is_absolute():
        warnings.append(f"{label} is absolute; avoid baking machine-specific paths into shared commands")
    if not candidate.exists():
        warnings.append(f"{label} does not exist on this machine: {path}")


def prefixed_command(cuda_visible_devices: str | None, parts: list[str]) -> list[str]:
    if cuda_visible_devices is None:
        return parts
    return [f"CUDA_VISIBLE_DEVICES={cuda_visible_devices}"] + parts


def build_train(args: argparse.Namespace) -> tuple[list[str], dict[str, object]]:
    n_classes = infer_n_classes(args.task, args.n_classes)
    embed_dim, warnings = resolve_embed_dim(args.embed_dim, args.encoder)
    warnings.extend(validate_model_task("train", args.task, args.model_type, n_classes, args.subtyping))
    maybe_check_dir(args.data_root_dir, "data_root_dir", warnings)
    if args.split_dir and (args.split_dir.startswith("splits/") or args.split_dir.startswith("./splits/")):
        warnings.append("main.py prefixes --split_dir with splits/; pass only the split directory basename")

    parts = [
        "python",
        "main.py",
        "--data_root_dir",
        args.data_root_dir,
        "--task",
        args.task,
        "--model_type",
        args.model_type,
        "--exp_code",
        args.exp_code,
        "--k",
        str(args.k),
        "--max_epochs",
        str(args.max_epochs),
        "--lr",
        str(args.lr),
        "--reg",
        str(args.reg),
        "--label_frac",
        str(args.label_frac),
        "--results_dir",
        args.results_dir,
        "--drop_out",
        str(args.drop_out),
        "--bag_loss",
        args.bag_loss,
        "--model_size",
        args.model_size,
        "--opt",
        args.opt,
        "--embed_dim",
        str(embed_dim),
    ]
    if args.split_dir:
        parts.extend(["--split_dir", args.split_dir])
    if args.k_start is not None:
        parts.extend(["--k_start", str(args.k_start)])
    if args.k_end is not None:
        parts.extend(["--k_end", str(args.k_end)])
    if args.seed != 1:
        parts.extend(["--seed", str(args.seed)])
    if args.weighted_sample:
        parts.append("--weighted_sample")
    if args.log_data:
        parts.append("--log_data")
    if args.early_stopping:
        parts.append("--early_stopping")
    if args.testing:
        parts.append("--testing")
    if args.model_type in {"clam_sb", "clam_mb"}:
        if args.no_inst_cluster:
            parts.append("--no_inst_cluster")
        if args.inst_loss != "none":
            parts.extend(["--inst_loss", args.inst_loss])
        parts.extend(["--bag_weight", str(args.bag_weight), "--B", str(args.B)])
        if args.subtyping:
            parts.append("--subtyping")
    if args.bag_loss == "svm" or args.inst_loss == "svm":
        warnings.append("SVM losses require smooth-topk/topk.svm at runtime")

    command = prefixed_command(args.cuda_visible_devices, parts)
    output_dir = f"{args.results_dir.rstrip('/')}/{args.exp_code}_s{args.seed}"
    summary = {
        "mode": "train",
        "command": command,
        "output_dir": output_dir,
        "summary_csv": f"{output_dir}/summary.csv",
        "checkpoint_pattern": f"{output_dir}/s_<fold>_checkpoint.pt",
        "n_classes": n_classes,
        "embed_dim": embed_dim,
        "warnings": warnings,
    }
    return command, summary


def build_eval(args: argparse.Namespace) -> tuple[list[str], dict[str, object]]:
    n_classes = infer_n_classes(args.task, args.n_classes)
    embed_dim, warnings = resolve_embed_dim(args.embed_dim, args.encoder)
    warnings.extend(validate_model_task("eval", args.task, args.model_type, n_classes, subtyping=True))
    maybe_check_dir(args.data_root_dir, "data_root_dir", warnings)
    maybe_check_dir(args.results_dir, "results_dir", warnings)
    if args.splits_dir:
        maybe_check_dir(args.splits_dir, "splits_dir", warnings)

    parts = [
        "python",
        "eval.py",
        "--data_root_dir",
        args.data_root_dir,
        "--results_dir",
        args.results_dir,
        "--models_exp_code",
        args.models_exp_code,
        "--save_exp_code",
        args.save_exp_code,
        "--task",
        args.task,
        "--model_type",
        args.model_type,
        "--model_size",
        args.model_size,
        "--drop_out",
        str(args.drop_out),
        "--k",
        str(args.k),
        "--split",
        args.split,
        "--embed_dim",
        str(embed_dim),
    ]
    if args.splits_dir:
        parts.extend(["--splits_dir", args.splits_dir])
    if args.k_start is not None:
        parts.extend(["--k_start", str(args.k_start)])
    if args.k_end is not None:
        parts.extend(["--k_end", str(args.k_end)])
    if args.fold is not None:
        parts.extend(["--fold", str(args.fold)])
    if args.micro_average:
        parts.append("--micro_average")

    command = prefixed_command(args.cuda_visible_devices, parts)
    models_dir = f"{args.results_dir.rstrip('/')}/{args.models_exp_code}"
    save_dir = f"eval_results/EVAL_{args.save_exp_code}"
    summary = {
        "mode": "eval",
        "command": command,
        "models_dir": models_dir,
        "checkpoint_pattern": f"{models_dir}/s_<fold>_checkpoint.pt",
        "save_dir": save_dir,
        "summary_csv": f"{save_dir}/summary.csv",
        "n_classes": n_classes,
        "embed_dim": embed_dim,
        "warnings": warnings,
    }
    return command, summary


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build safe CLAM training/evaluation commands.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    train = subparsers.add_parser("train", help="render a main.py training command")
    add_common(train)
    train.add_argument("--data-root-dir", required=True)
    train.add_argument("--exp-code", required=True)
    train.add_argument("--results-dir", default="./results")
    train.add_argument("--split-dir", default=None, help="basename under splits/, not a full path")
    train.add_argument("--k", type=positive_int, default=10)
    train.add_argument("--k-start", type=nonnegative_int, default=None)
    train.add_argument("--k-end", type=nonnegative_int, default=None)
    train.add_argument("--seed", type=int, default=1)
    train.add_argument("--max-epochs", type=positive_int, default=200)
    train.add_argument("--lr", type=float, default=1e-4)
    train.add_argument("--reg", type=float, default=1e-5)
    train.add_argument("--label-frac", type=fraction, default=1.0)
    train.add_argument("--opt", choices=("adam", "sgd"), default="adam")
    train.add_argument("--bag-loss", choices=("ce", "svm"), default="ce")
    train.add_argument("--inst-loss", choices=("none", "ce", "svm"), default="none")
    train.add_argument("--weighted-sample", action="store_true")
    train.add_argument("--log-data", action="store_true")
    train.add_argument("--early-stopping", action="store_true")
    train.add_argument("--testing", action="store_true")
    train.add_argument("--no-inst-cluster", action="store_true")
    train.add_argument("--subtyping", action="store_true")
    train.add_argument("--bag-weight", type=float, default=0.7)
    train.add_argument("--B", type=positive_int, default=8)
    train.set_defaults(builder=build_train)

    evaluate = subparsers.add_parser("eval", help="render an eval.py checkpoint evaluation command")
    add_common(evaluate)
    evaluate.add_argument("--data-root-dir", required=True)
    evaluate.add_argument("--results-dir", default="./results")
    evaluate.add_argument("--models-exp-code", required=True)
    evaluate.add_argument("--save-exp-code", required=True)
    evaluate.add_argument("--splits-dir", default=None)
    evaluate.add_argument("--k", type=positive_int, default=10)
    evaluate.add_argument("--k-start", type=nonnegative_int, default=None)
    evaluate.add_argument("--k-end", type=nonnegative_int, default=None)
    evaluate.add_argument("--fold", type=nonnegative_int, default=None)
    evaluate.add_argument("--split", choices=("train", "val", "test", "all"), default="test")
    evaluate.add_argument("--micro-average", action="store_true")
    evaluate.set_defaults(builder=build_eval)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        command, summary = args.builder(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.output_mode == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Command:")
        print(quote_command(command))
        print("Expected outputs:")
        for key in ("output_dir", "models_dir", "save_dir", "summary_csv", "checkpoint_pattern"):
            if key in summary:
                print(f"- {key}: {summary[key]}")
        if summary["warnings"]:
            print("Warnings:")
            for warning in summary["warnings"]:
                print(f"- {warning}")
        print("Reminder: this helper only renders commands; it does not run CLAM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

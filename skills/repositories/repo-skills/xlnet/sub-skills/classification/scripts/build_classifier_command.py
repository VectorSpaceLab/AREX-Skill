#!/usr/bin/env python3
"""Print a safe XLNet run_classifier.py command.

This helper only renders a shell command. It does not download data, import
TensorFlow, open checkpoints, create directories, or launch training.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from typing import Dict, Iterable, List, Optional, Set

TASKS = ("mnli_matched", "mnli_mismatched", "sts-b", "imdb", "yelp5")
MODES = {
    "train": {"train"},
    "eval": {"eval"},
    "predict": {"predict"},
    "train_eval": {"train", "eval"},
    "eval_predict": {"eval", "predict"},
    "train_eval_predict": {"train", "eval", "predict"},
}

PRESETS: Dict[str, Dict[str, object]] = {
    "stsb-gpu-large": {
        "task_name": "sts-b",
        "backend": "gpu",
        "default_mode": "train",
        "max_seq_length": 128,
        "train_batch_size": 8,
        "eval_batch_size": 8,
        "learning_rate": 5e-5,
        "train_steps": 1200,
        "warmup_steps": 120,
        "save_steps": 600,
        "is_regression": True,
        "num_hosts": 1,
        "eval_all_ckpt": True,
    },
    "imdb-tpu-large": {
        "task_name": "imdb",
        "backend": "tpu",
        "default_mode": "train_eval",
        "max_seq_length": 512,
        "train_batch_size": 32,
        "eval_batch_size": 8,
        "learning_rate": 2e-5,
        "train_steps": 4000,
        "warmup_steps": 500,
        "save_steps": 500,
        "iterations": 500,
        "num_hosts": 1,
        "num_core_per_host": 8,
        "eval_all_ckpt": True,
    },
    "colab-imdb-gpu": {
        "task_name": "imdb",
        "backend": "gpu",
        "default_mode": "train_eval",
        "max_seq_length": 128,
        "train_batch_size": 8,
        "eval_batch_size": 8,
        "learning_rate": 2e-5,
        "train_steps": 4000,
        "warmup_steps": 500,
        "save_steps": 500,
        "iterations": 500,
        "num_hosts": 1,
        "num_core_per_host": 1,
        "eval_all_ckpt": True,
    },
}


def add_bool_pair(parser: argparse.ArgumentParser, name: str, dest: str, help_text: str) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--" + name, dest=dest, action="store_true", default=None, help=help_text)
    group.add_argument("--no-" + name, dest=dest, action="store_false", help=argparse.SUPPRESS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a python run_classifier.py command for XLNet classification/regression tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # STS-B train on 4 GPUs, using README hyperparameters.
  %(prog)s --preset stsb-gpu-large --mode train --data-dir GLUE/STS-B \
    --output-dir proc_data/sts-b --model-dir exp/sts-b \
    --model-config-path xlnet_config.json --spiece-model-file spiece.model \
    --init-checkpoint xlnet_model.ckpt --cuda-visible-devices 0,1,2,3

  # Evaluate all STS-B checkpoints on one GPU; init_checkpoint is intentionally omitted.
  %(prog)s --preset stsb-gpu-large --mode eval --data-dir GLUE/STS-B \
    --output-dir proc_data/sts-b --model-dir exp/sts-b \
    --model-config-path xlnet_config.json --spiece-model-file spiece.model \
    --eval-all-ckpt --cuda-visible-devices 0
""",
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Optional README/notebook recipe preset.")
    parser.add_argument("--task-name", dest="task_name", choices=TASKS, help="run_classifier.py task_name.")
    parser.add_argument("--mode", choices=sorted(MODES), help="Which do_train/do_eval/do_predict flags to enable.")
    parser.add_argument("--backend", choices=("cpu", "gpu", "tpu"), help="Backend command shape to generate.")
    parser.add_argument("--python", default="python", help="Python executable token to print. Default: python.")
    parser.add_argument("--script-path", default="run_classifier.py", help="Path to the caller's run_classifier.py. Default: run_classifier.py.")
    parser.add_argument("--format", choices=("multiline", "single-line"), default="multiline", help="Command rendering style.")

    # Required-by-script paths are validated after preset/default processing.
    parser.add_argument("--data-dir", dest="data_dir", help="Raw task data directory.")
    parser.add_argument("--output-dir", dest="output_dir", help="TFRecord cache directory.")
    parser.add_argument("--model-dir", dest="model_dir", help="Fine-tuned checkpoint/event directory.")
    parser.add_argument("--model-config-path", dest="model_config_path", help="XLNet config JSON path.")
    parser.add_argument("--spiece-model-file", dest="spiece_model_file", help="SentencePiece model path.")
    parser.add_argument("--init-checkpoint", dest="init_checkpoint", help="Checkpoint prefix for model initialization, normally required for training.")
    parser.add_argument("--include-init-checkpoint-for-eval", action="store_true", help="Include init_checkpoint even for eval/predict-only commands. Usually leave off.")

    parser.add_argument("--cuda-visible-devices", help="Prefix GPU commands with CUDA_VISIBLE_DEVICES=<value>.")
    parser.add_argument("--tpu", help="Cloud TPU name for --use_tpu=True commands.")
    parser.add_argument("--tpu-zone", dest="tpu_zone", help="Cloud TPU zone.")
    parser.add_argument("--gcp-project", dest="gcp_project", help="GCP project for TPU resolver.")
    parser.add_argument("--tpu-job-name", dest="tpu_job_name", help="TPU worker job name.")
    parser.add_argument("--master", help="TensorFlow master string.")
    parser.add_argument("--num-hosts", dest="num_hosts", type=int, help="Number of hosts.")
    parser.add_argument("--num-core-per-host", dest="num_core_per_host", type=int, help="GPUs per host or TPU cores per host.")
    parser.add_argument("--iterations", type=int, help="Iterations per TPU loop; also accepted by GPU/CPU RunConfig.")

    parser.add_argument("--max-seq-length", dest="max_seq_length", type=int, help="Maximum sequence length.")
    parser.add_argument("--train-batch-size", dest="train_batch_size", type=int, help="Training batch size; per GPU for multi-GPU.")
    parser.add_argument("--eval-batch-size", dest="eval_batch_size", type=int, help="Eval batch size.")
    parser.add_argument("--predict-batch-size", dest="predict_batch_size", type=int, help="Predict batch size.")
    parser.add_argument("--learning-rate", dest="learning_rate", type=float, help="Initial learning rate.")
    parser.add_argument("--train-steps", dest="train_steps", type=int, help="Training steps.")
    parser.add_argument("--warmup-steps", dest="warmup_steps", type=int, help="Warmup steps.")
    parser.add_argument("--save-steps", dest="save_steps", type=int, help="Checkpoint save interval.")
    parser.add_argument("--max-save", dest="max_save", type=int, help="Max checkpoints to keep; 0 means keep all.")
    parser.add_argument("--num-passes", dest="num_passes", type=int, help="Passes over train examples during preprocessing.")
    parser.add_argument("--shuffle-buffer", dest="shuffle_buffer", type=int, help="Training shuffle buffer.")
    parser.add_argument("--eval-split", dest="eval_split", choices=("dev", "test"), help="Split for eval/predict.")
    parser.add_argument("--predict-dir", dest="predict_dir", help="Prediction output directory; required for predict mode.")
    parser.add_argument("--predict-ckpt", dest="predict_ckpt", help="Explicit checkpoint prefix for prediction.")
    parser.add_argument("--predict-threshold", dest="predict_threshold", type=float, help="Binary prediction threshold.")

    parser.add_argument("--dropout", type=float, help="Dropout rate.")
    parser.add_argument("--dropatt", type=float, help="Attention dropout rate.")
    parser.add_argument("--clamp-len", dest="clamp_len", type=int, help="Clamp length.")
    parser.add_argument("--summary-type", dest="summary_type", help="Sequence summary type.")
    parser.add_argument("--cls-scope", dest="cls_scope", help="Classifier variable scope.")
    parser.add_argument("--lr-layer-decay-rate", dest="lr_layer_decay_rate", type=float, help="Layer-wise LR decay rate.")
    parser.add_argument("--min-lr-ratio", dest="min_lr_ratio", type=float, help="Minimum LR ratio for decay.")
    parser.add_argument("--clip", type=float, help="Global gradient clip norm.")
    parser.add_argument("--weight-decay", dest="weight_decay", type=float, help="Weight decay rate.")
    parser.add_argument("--adam-epsilon", dest="adam_epsilon", type=float, help="Adam epsilon.")
    parser.add_argument("--decay-method", dest="decay_method", choices=("poly", "cos"), help="LR decay method.")

    add_bool_pair(parser, "uncased", "uncased", "Set --uncased=True in the generated command.")
    add_bool_pair(parser, "is-regression", "is_regression", "Set --is_regression=True. Automatically enabled for sts-b.")
    add_bool_pair(parser, "eval-all-ckpt", "eval_all_ckpt", "Set --eval_all_ckpt=True when eval is enabled.")
    add_bool_pair(parser, "overwrite-data", "overwrite_data", "Set --overwrite_data=True to rebuild TFRecords.")
    add_bool_pair(parser, "use-bfloat16", "use_bfloat16", "Set --use_bfloat16=True.")
    add_bool_pair(parser, "use-summ-proj", "use_summ_proj", "Set --use_summ_proj=True/False.")
    return parser


def set_if_none(args: argparse.Namespace, name: str, value: object) -> None:
    if getattr(args, name) is None:
        setattr(args, name, value)


def cuda_device_count(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    items = [part.strip() for part in value.split(",") if part.strip()]
    return len(items) or None


def warn(message: str) -> None:
    print("warning: " + message, file=sys.stderr)


def normalize_for_warning(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return path.rstrip("/")


def apply_defaults(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Set[str]:
    user_set_eval_all_ckpt = args.eval_all_ckpt is not None
    preset = PRESETS.get(args.preset or "")
    if preset:
        for key, value in preset.items():
            if key == "default_mode":
                continue
            set_if_none(args, key, value)

    if args.mode is None:
        args.mode = str(preset.get("default_mode", "train")) if preset else "train"
    actions = MODES[args.mode]

    set_if_none(args, "backend", "gpu")
    set_if_none(args, "max_seq_length", 128)
    set_if_none(args, "train_batch_size", 8)
    set_if_none(args, "eval_batch_size", 128)
    set_if_none(args, "predict_batch_size", 128)
    set_if_none(args, "learning_rate", 1e-5)
    set_if_none(args, "train_steps", 1000)
    set_if_none(args, "warmup_steps", 0)
    set_if_none(args, "num_hosts", 1)
    set_if_none(args, "iterations", 1000)
    set_if_none(args, "num_passes", 1)
    set_if_none(args, "eval_split", "dev")
    set_if_none(args, "uncased", False)
    set_if_none(args, "eval_all_ckpt", False)
    set_if_none(args, "overwrite_data", False)
    set_if_none(args, "use_bfloat16", False)
    set_if_none(args, "use_summ_proj", True)

    if args.num_core_per_host is None:
        if args.backend == "tpu":
            args.num_core_per_host = 8
        elif args.backend == "gpu":
            if args.preset == "stsb-gpu-large" and actions == {"train"}:
                args.num_core_per_host = cuda_device_count(args.cuda_visible_devices) or 4
            else:
                args.num_core_per_host = cuda_device_count(args.cuda_visible_devices) or 1
        else:
            args.num_core_per_host = 1

    if args.task_name == "sts-b":
        if args.is_regression is False:
            parser.error("sts-b requires --is-regression; do not pass --no-is-regression")
        args.is_regression = True
    else:
        set_if_none(args, "is_regression", False)

    required = [
        ("task_name", "--task-name (or a preset that sets it)"),
        ("data_dir", "--data-dir"),
        ("output_dir", "--output-dir"),
        ("model_dir", "--model-dir"),
        ("model_config_path", "--model-config-path"),
        ("spiece_model_file", "--spiece-model-file"),
    ]
    for attr, flag in required:
        if not getattr(args, attr):
            parser.error(f"{flag} is required")

    if "train" in actions and not args.init_checkpoint:
        parser.error("--init-checkpoint is required for train modes")
    if "predict" in actions and not args.predict_dir:
        parser.error("--predict-dir is required for predict modes")
    if args.backend == "tpu" and not (args.tpu or args.master):
        warn("TPU backend selected without --tpu or --master; fill in TPU resolver details before running the printed command.")
    if args.backend == "cpu" and "train" in actions:
        warn("CPU training is usually impractically slow; use this only for tiny smoke runs or command adaptation.")
    if args.backend == "gpu" and "eval" in actions and args.num_core_per_host != 1:
        warn("The documented XLNet workflow evaluates on one GPU; consider --num-core-per-host 1 for eval.")
    if args.backend == "gpu" and args.cuda_visible_devices:
        count = cuda_device_count(args.cuda_visible_devices)
        if count and count != args.num_core_per_host:
            warn("CUDA_VISIBLE_DEVICES count differs from --num-core-per-host; make them match for multi-GPU training.")
    if args.is_regression and args.task_name != "sts-b":
        warn("--is_regression=True with a non-STS-B built-in task changes the loss/schema; verify that this is intentional.")
    if args.eval_all_ckpt and "eval" not in actions and user_set_eval_all_ckpt:
        warn("--eval-all-ckpt has no effect without eval mode.")
    if args.eval_all_ckpt and "train" in actions and args.save_steps is None:
        warn("eval_all_ckpt is most useful when training saves checkpoints; consider --save-steps.")

    init_norm = normalize_for_warning(args.init_checkpoint)
    model_norm = normalize_for_warning(args.model_dir)
    if init_norm and model_norm:
        init_parent = normalize_for_warning(os.path.dirname(init_norm))
        if init_norm == model_norm or init_parent == model_norm:
            warn("init_checkpoint appears to be the same as or inside model_dir; keep pretrained init checkpoints separate from fine-tuned model_dir unless deliberately resuming.")

    if args.init_checkpoint and "train" not in actions and not args.include_init_checkpoint_for_eval:
        warn("omitting --init_checkpoint from eval/predict-only command; pass --include-init-checkpoint-for-eval to force it.")

    return actions


def bool_string(value: bool) -> str:
    return "True" if value else "False"


def add_flag(parts: List[str], name: str, value: object, include_if_none: bool = False) -> None:
    if value is None and not include_if_none:
        return
    if isinstance(value, bool):
        rendered = bool_string(value)
    else:
        rendered = str(value)
    parts.append(f"--{name}={rendered}")


def build_command(args: argparse.Namespace, actions: Set[str]) -> List[str]:
    parts: List[str] = []
    if args.backend == "gpu" and args.cuda_visible_devices:
        parts.append("CUDA_VISIBLE_DEVICES=" + args.cuda_visible_devices)
    parts.extend([args.python, args.script_path])

    add_flag(parts, "do_train", "train" in actions)
    add_flag(parts, "do_eval", "eval" in actions)
    add_flag(parts, "do_predict", "predict" in actions)
    add_flag(parts, "task_name", args.task_name)
    add_flag(parts, "data_dir", args.data_dir)
    add_flag(parts, "output_dir", args.output_dir)
    add_flag(parts, "model_dir", args.model_dir)
    add_flag(parts, "uncased", args.uncased)
    add_flag(parts, "spiece_model_file", args.spiece_model_file)
    add_flag(parts, "model_config_path", args.model_config_path)

    if args.init_checkpoint and ("train" in actions or args.include_init_checkpoint_for_eval):
        add_flag(parts, "init_checkpoint", args.init_checkpoint)

    add_flag(parts, "use_tpu", args.backend == "tpu")
    add_flag(parts, "num_hosts", args.num_hosts)
    add_flag(parts, "num_core_per_host", args.num_core_per_host)
    add_flag(parts, "iterations", args.iterations)
    for out_name, attr in [
        ("tpu", "tpu"),
        ("tpu_zone", "tpu_zone"),
        ("gcp_project", "gcp_project"),
        ("tpu_job_name", "tpu_job_name"),
        ("master", "master"),
    ]:
        add_flag(parts, out_name, getattr(args, attr))

    add_flag(parts, "max_seq_length", args.max_seq_length)
    add_flag(parts, "num_passes", args.num_passes)
    add_flag(parts, "is_regression", True if args.is_regression else None)
    add_flag(parts, "overwrite_data", True if args.overwrite_data else None)

    if "train" in actions:
        for out_name, attr in [
            ("train_batch_size", "train_batch_size"),
            ("learning_rate", "learning_rate"),
            ("train_steps", "train_steps"),
            ("warmup_steps", "warmup_steps"),
            ("save_steps", "save_steps"),
            ("max_save", "max_save"),
            ("shuffle_buffer", "shuffle_buffer"),
            ("lr_layer_decay_rate", "lr_layer_decay_rate"),
            ("min_lr_ratio", "min_lr_ratio"),
            ("clip", "clip"),
            ("weight_decay", "weight_decay"),
            ("adam_epsilon", "adam_epsilon"),
            ("decay_method", "decay_method"),
        ]:
            add_flag(parts, out_name, getattr(args, attr))

    if "eval" in actions:
        add_flag(parts, "eval_batch_size", args.eval_batch_size)
        add_flag(parts, "eval_split", args.eval_split)
        add_flag(parts, "eval_all_ckpt", True if args.eval_all_ckpt else None)

    if "predict" in actions:
        add_flag(parts, "predict_batch_size", args.predict_batch_size)
        add_flag(parts, "eval_split", args.eval_split)
        add_flag(parts, "predict_dir", args.predict_dir)
        add_flag(parts, "predict_ckpt", args.predict_ckpt)
        add_flag(parts, "predict_threshold", args.predict_threshold)

    for out_name, attr in [
        ("dropout", "dropout"),
        ("dropatt", "dropatt"),
        ("clamp_len", "clamp_len"),
        ("summary_type", "summary_type"),
        ("cls_scope", "cls_scope"),
    ]:
        add_flag(parts, out_name, getattr(args, attr))
    add_flag(parts, "use_bfloat16", True if args.use_bfloat16 else None)
    if args.use_summ_proj is not True:
        add_flag(parts, "use_summ_proj", args.use_summ_proj)

    return parts


def render_command(parts: Iterable[str], style: str) -> str:
    quoted = [shlex.quote(part) for part in parts]
    if style == "single-line":
        return " ".join(quoted)
    return " \\\n  ".join(quoted)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    actions = apply_defaults(parser, args)
    command = build_command(args, actions)
    print(render_command(command, args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

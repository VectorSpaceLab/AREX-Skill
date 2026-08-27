#!/usr/bin/env python3
"""Print safe XLNet SQuAD run_squad.py commands.

The generator never executes the command and does not touch the filesystem. It
turns the XLNet SQuAD preprocessing/GPU/TPU recipes into explicit commands with
user-supplied paths.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional


def q(value: object) -> str:
    return shlex.quote(str(value))


def bool_str(value: bool) -> str:
    return "True" if value else "False"


def add_flag(parts: List[str], name: str, value: object) -> None:
    if value is None:
        return
    parts.append(f"--{name}={q(value)}")


def build_command(args: argparse.Namespace, *, proc_id: Optional[int] = None) -> List[str]:
    parts: List[str] = [q(args.python), q(args.runner)]

    if args.mode == "prepro":
        add_flag(parts, "use_tpu", "False")
        add_flag(parts, "do_prepro", "True")
        add_flag(parts, "spiece_model_file", args.spiece_model_file)
        add_flag(parts, "train_file", args.train_file)
        add_flag(parts, "output_dir", args.output_dir)
        add_flag(parts, "uncased", bool_str(args.uncased))
        add_flag(parts, "max_seq_length", args.max_seq_length)
        add_flag(parts, "max_query_length", args.max_query_length)
        add_flag(parts, "doc_stride", args.doc_stride)
        add_flag(parts, "num_proc", args.num_proc)
        add_flag(parts, "proc_id", args.proc_id if proc_id is None else proc_id)
        add_flag(parts, "overwrite_data", bool_str(args.overwrite_data))
        return parts + args.extra_arg

    if args.mode == "gpu-base":
        add_flag(parts, "use_tpu", "False")
        add_flag(parts, "num_hosts", args.num_hosts)
        add_flag(parts, "num_core_per_host", args.num_core_per_host)
        add_flag(parts, "model_config_path", args.model_config_path)
        add_flag(parts, "spiece_model_file", args.spiece_model_file)
        add_flag(parts, "output_dir", args.output_dir)
        add_flag(parts, "init_checkpoint", args.init_checkpoint)
        add_flag(parts, "model_dir", args.model_dir)
        add_flag(parts, "train_file", args.train_file)
        add_flag(parts, "predict_file", args.predict_file)
        add_flag(parts, "predict_dir", args.predict_dir)
        add_flag(parts, "uncased", bool_str(args.uncased))
        add_flag(parts, "max_seq_length", args.max_seq_length)
        add_flag(parts, "max_query_length", args.max_query_length)
        add_flag(parts, "doc_stride", args.doc_stride)
        add_flag(parts, "max_answer_length", args.max_answer_length)
        add_flag(parts, "do_train", "True")
        add_flag(parts, "train_batch_size", args.train_batch_size)
        add_flag(parts, "do_predict", "True")
        add_flag(parts, "predict_batch_size", args.predict_batch_size)
        add_flag(parts, "learning_rate", args.learning_rate)
        add_flag(parts, "adam_epsilon", args.adam_epsilon)
        add_flag(parts, "iterations", args.iterations)
        add_flag(parts, "save_steps", args.save_steps)
        add_flag(parts, "train_steps", args.train_steps)
        add_flag(parts, "warmup_steps", args.warmup_steps)
        add_flag(parts, "n_best_size", args.n_best_size)
        add_flag(parts, "start_n_top", args.start_n_top)
        add_flag(parts, "end_n_top", args.end_n_top)
        add_flag(parts, "target_eval_key", args.target_eval_key)
        add_flag(parts, "overwrite_data", bool_str(args.overwrite_data))
        return parts + args.extra_arg

    if args.mode == "tpu-large":
        add_flag(parts, "use_tpu", "True")
        add_flag(parts, "tpu", args.tpu)
        add_flag(parts, "tpu_zone", args.tpu_zone)
        add_flag(parts, "gcp_project", args.gcp_project)
        add_flag(parts, "master", args.master)
        add_flag(parts, "tpu_job_name", args.tpu_job_name)
        add_flag(parts, "num_hosts", args.num_hosts)
        add_flag(parts, "num_core_per_host", args.num_core_per_host)
        add_flag(parts, "model_config_path", args.model_config_path)
        add_flag(parts, "spiece_model_file", args.spiece_model_file)
        add_flag(parts, "output_dir", args.output_dir)
        add_flag(parts, "init_checkpoint", args.init_checkpoint)
        add_flag(parts, "model_dir", args.model_dir)
        add_flag(parts, "train_file", args.train_file)
        add_flag(parts, "predict_file", args.predict_file)
        add_flag(parts, "predict_dir", args.predict_dir)
        add_flag(parts, "uncased", bool_str(args.uncased))
        add_flag(parts, "max_seq_length", args.max_seq_length)
        add_flag(parts, "max_query_length", args.max_query_length)
        add_flag(parts, "doc_stride", args.doc_stride)
        add_flag(parts, "max_answer_length", args.max_answer_length)
        add_flag(parts, "use_bfloat16", bool_str(args.use_bfloat16))
        add_flag(parts, "do_train", "True")
        add_flag(parts, "train_batch_size", args.train_batch_size)
        add_flag(parts, "do_predict", "True")
        add_flag(parts, "predict_batch_size", args.predict_batch_size)
        add_flag(parts, "learning_rate", args.learning_rate)
        add_flag(parts, "adam_epsilon", args.adam_epsilon)
        add_flag(parts, "iterations", args.iterations)
        add_flag(parts, "save_steps", args.save_steps)
        add_flag(parts, "train_steps", args.train_steps)
        add_flag(parts, "warmup_steps", args.warmup_steps)
        add_flag(parts, "n_best_size", args.n_best_size)
        add_flag(parts, "start_n_top", args.start_n_top)
        add_flag(parts, "end_n_top", args.end_n_top)
        add_flag(parts, "target_eval_key", args.target_eval_key)
        add_flag(parts, "overwrite_data", bool_str(args.overwrite_data))
        return parts + args.extra_arg

    if args.mode == "predict-only":
        add_flag(parts, "use_tpu", bool_str(args.use_tpu_predict))
        add_flag(parts, "tpu", args.tpu if args.use_tpu_predict else None)
        add_flag(parts, "tpu_zone", args.tpu_zone if args.use_tpu_predict else None)
        add_flag(parts, "gcp_project", args.gcp_project if args.use_tpu_predict else None)
        add_flag(parts, "master", args.master if args.use_tpu_predict else None)
        add_flag(parts, "tpu_job_name", args.tpu_job_name if args.use_tpu_predict else None)
        add_flag(parts, "num_hosts", args.num_hosts)
        add_flag(parts, "num_core_per_host", args.num_core_per_host)
        add_flag(parts, "model_config_path", args.model_config_path)
        add_flag(parts, "spiece_model_file", args.spiece_model_file)
        add_flag(parts, "output_dir", args.output_dir)
        add_flag(parts, "model_dir", args.model_dir)
        add_flag(parts, "predict_file", args.predict_file)
        add_flag(parts, "predict_dir", args.predict_dir)
        add_flag(parts, "uncased", bool_str(args.uncased))
        add_flag(parts, "max_seq_length", args.max_seq_length)
        add_flag(parts, "max_query_length", args.max_query_length)
        add_flag(parts, "doc_stride", args.doc_stride)
        add_flag(parts, "max_answer_length", args.max_answer_length)
        add_flag(parts, "do_train", "False")
        add_flag(parts, "do_predict", "True")
        add_flag(parts, "predict_batch_size", args.predict_batch_size)
        add_flag(parts, "n_best_size", args.n_best_size)
        add_flag(parts, "start_n_top", args.start_n_top)
        add_flag(parts, "end_n_top", args.end_n_top)
        add_flag(parts, "target_eval_key", args.target_eval_key)
        add_flag(parts, "overwrite_data", bool_str(args.overwrite_data))
        return parts + args.extra_arg

    raise AssertionError(args.mode)


def format_command(parts: Iterable[str]) -> str:
    parts = list(parts)
    if len(parts) <= 2:
        return " ".join(parts)
    lines = [" ".join(parts[:2]) + " \\"]
    for idx, part in enumerate(parts[2:]):
        suffix = " \\" if idx < len(parts[2:]) - 1 else ""
        lines.append(f"  {part}{suffix}")
    return "\n".join(lines)


def require(parser: argparse.ArgumentParser, args: argparse.Namespace, names: Iterable[str]) -> None:
    missing = [name for name in names if getattr(args, name) in (None, "")]
    if missing:
        parser.error("missing required argument(s) for {mode}: {items}".format(
            mode=args.mode,
            items=", ".join("--" + name.replace("_", "-") for name in missing),
        ))


def validate(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    positive_fields = [
        "max_seq_length", "max_query_length", "doc_stride", "max_answer_length",
        "num_proc", "num_hosts", "num_core_per_host", "train_batch_size",
        "predict_batch_size", "iterations", "train_steps", "warmup_steps",
        "n_best_size", "start_n_top", "end_n_top",
    ]
    for name in positive_fields:
        value = getattr(args, name, None)
        if value is not None and value < 1:
            parser.error(f"--{name.replace('_', '-')} must be >= 1")

    if args.proc_id < 0:
        parser.error("--proc-id must be >= 0")
    if args.proc_id >= args.num_proc:
        parser.error("--proc-id must be smaller than --num-proc")
    if args.emit_all_proc_ids and args.mode != "prepro":
        parser.error("--emit-all-proc-ids is only valid with --mode prepro")
    if args.emit_all_proc_ids and args.num_proc < 2:
        parser.error("--emit-all-proc-ids requires --num-proc >= 2")
    for item in args.extra_arg:
        if not item.startswith("--"):
            parser.error("--extra-arg values must look like run_squad.py flags and start with '--'")

    if args.mode == "prepro":
        require(parser, args, ["spiece_model_file", "train_file", "output_dir"])
    elif args.mode == "gpu-base":
        require(parser, args, [
            "model_config_path", "spiece_model_file", "output_dir", "init_checkpoint",
            "model_dir", "train_file", "predict_file", "predict_dir",
        ])
    elif args.mode == "tpu-large":
        require(parser, args, [
            "tpu", "model_config_path", "spiece_model_file", "output_dir",
            "init_checkpoint", "model_dir", "train_file", "predict_file", "predict_dir",
        ])
        gcs_fields = ["output_dir", "init_checkpoint", "model_dir", "predict_dir"]
        not_gcs = [name for name in gcs_fields if not str(getattr(args, name)).startswith("gs://")]
        if not_gcs and not args.allow_non_gcs_tpu_paths:
            parser.error(
                "TPU-large mode expects GCS paths for --output-dir, --init-checkpoint, "
                "--model-dir, and --predict-dir; pass --allow-non-gcs-tpu-paths only if your TPU setup can read them."
            )
    elif args.mode == "predict-only":
        require(parser, args, [
            "model_config_path", "spiece_model_file", "output_dir", "model_dir",
            "predict_file", "predict_dir",
        ])
        if args.init_checkpoint:
            parser.error("predict-only does not use --init-checkpoint; put the fine-tuned checkpoint under --model-dir")
        if args.use_tpu_predict and not args.tpu:
            parser.error("--use-tpu-predict requires --tpu")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print run_squad.py commands for XLNet SQuAD preprocessing, training, and prediction."
    )
    parser.add_argument("--mode", choices=["prepro", "gpu-base", "tpu-large", "predict-only"], required=True)
    parser.add_argument("--python", default="python", help="Python executable to print in the command.")
    parser.add_argument("--runner", default="run_squad.py", help="Path to run_squad.py, usually relative to the XLNet checkout root.")

    parser.add_argument("--model-config-path")
    parser.add_argument("--spiece-model-file")
    parser.add_argument("--init-checkpoint")
    parser.add_argument("--output-dir")
    parser.add_argument("--predict-dir")
    parser.add_argument("--model-dir")
    parser.add_argument("--train-file")
    parser.add_argument("--predict-file")

    parser.add_argument("--max-seq-length", type=int, default=512)
    parser.add_argument("--max-query-length", type=int, default=64)
    parser.add_argument("--doc-stride", type=int, default=128)
    parser.add_argument("--max-answer-length", type=int, default=64)
    parser.add_argument("--uncased", action="store_true", help="Set --uncased=True; omit for cased XLNet checkpoints.")
    parser.add_argument("--overwrite-data", action="store_true")

    parser.add_argument("--num-proc", type=int, default=1)
    parser.add_argument("--proc-id", type=int, default=0)
    parser.add_argument("--emit-all-proc-ids", action="store_true", help="For preprocessing, print one command per proc_id in 0..num_proc-1.")

    parser.add_argument("--num-hosts", type=int, default=1)
    parser.add_argument("--num-core-per-host", type=int)
    parser.add_argument("--tpu")
    parser.add_argument("--tpu-zone")
    parser.add_argument("--gcp-project")
    parser.add_argument("--master")
    parser.add_argument("--tpu-job-name")
    parser.add_argument("--use-bfloat16", action="store_true")
    parser.add_argument("--use-tpu-predict", action="store_true", help="Use TPUEstimator for predict-only commands.")
    parser.add_argument("--allow-non-gcs-tpu-paths", action="store_true")

    parser.add_argument("--train-batch-size", type=int)
    parser.add_argument("--predict-batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", default=None)
    parser.add_argument("--adam-epsilon", default="1e-6")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--save-steps", type=int, default=1000)
    parser.add_argument("--train-steps", type=int)
    parser.add_argument("--warmup-steps", type=int)

    parser.add_argument("--n-best-size", type=int, default=5)
    parser.add_argument("--start-n-top", type=int, default=5)
    parser.add_argument("--end-n-top", type=int, default=5)
    parser.add_argument("--target-eval-key", default="best_f1")
    parser.add_argument("--extra-arg", action="append", default=[], help="Additional quoted run_squad.py flag, e.g. --extra-arg=--dropout=0.05")
    return parser


def apply_recipe_defaults(args: argparse.Namespace) -> None:
    if args.mode == "gpu-base":
        if args.num_core_per_host is None:
            args.num_core_per_host = 3
        if args.train_batch_size is None:
            args.train_batch_size = 8
        if args.learning_rate is None:
            args.learning_rate = "2e-5"
        if args.train_steps is None:
            args.train_steps = 12000
        if args.warmup_steps is None:
            args.warmup_steps = 1000
    elif args.mode == "tpu-large":
        if args.num_core_per_host is None:
            args.num_core_per_host = 8
        if args.train_batch_size is None:
            args.train_batch_size = 48
        if args.learning_rate is None:
            args.learning_rate = "3e-5"
        if args.train_steps is None:
            args.train_steps = 8000
        if args.warmup_steps is None:
            args.warmup_steps = 1000
    else:
        if args.num_core_per_host is None:
            args.num_core_per_host = 1
        if args.train_batch_size is None:
            args.train_batch_size = 48
        if args.learning_rate is None:
            args.learning_rate = "3e-5"
        if args.train_steps is None:
            args.train_steps = 8000
        if args.warmup_steps is None:
            args.warmup_steps = 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    apply_recipe_defaults(args)
    validate(parser, args)

    if args.emit_all_proc_ids:
        for proc_id in range(args.num_proc):
            if proc_id:
                print()
            print(format_command(build_command(args, proc_id=proc_id)))
    else:
        print(format_command(build_command(args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

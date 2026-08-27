#!/usr/bin/env python3
"""Print safe XLNet RACE commands adapted from the TPU templates.

The helper performs argument validation and prints a shell-quoted command for
`run_race.py`. It never executes the command, starts a TPU job, writes GCS, or
reads the RACE dataset unless --validate-local-paths is explicitly requested.
"""

from __future__ import print_function

import argparse
import shlex
import sys
from pathlib import Path


PROFILES = {
    "tpu-v3-8": {
        "help": "TPU v3-8 recipe adapted from the batch-size-8 RACE template.",
        "num_hosts": 1,
        "num_core_per_host": 8,
        "train_batch_size": 8,
        "eval_batch_size": 32,
    },
    "tpu-v3-32": {
        "help": "TPU v3-32/pod recipe adapted from the batch-size-32 RACE template.",
        "num_hosts": 4,
        "num_core_per_host": 8,
        "train_batch_size": 32,
        "eval_batch_size": 32,
    },
}


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def nonnegative_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def number(value):
    try:
        float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be numeric")
    return value


def require_gcs(value, label):
    if not value or not value.startswith("gs://") or len(value) <= len("gs://"):
        raise ValueError("{} must be a non-empty GCS path beginning with gs://".format(label))
    return value.rstrip("/")


def join_gcs(root, *parts):
    root = require_gcs(root, "gcs root")
    clean_parts = [str(part).strip("/") for part in parts if str(part).strip("/")]
    if not clean_parts:
        return root
    return root + "/" + "/".join(clean_parts)


def bool_text(value):
    return "True" if value else "False"


def validate_existing_dir(value, label):
    path = Path(value).expanduser()
    if not path.is_dir():
        raise ValueError("{} does not exist or is not a directory: {}".format(label, value))


def validate_existing_file(value, label):
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError("{} does not exist or is not a file: {}".format(label, value))


def validate_args(args):
    if not args.do_train and not args.do_eval:
        raise ValueError("at least one phase must be enabled; do not combine --no-train and --no-eval")

    if args.high_only and args.middle_only:
        raise ValueError("choose at most one of --high-only and --middle-only")

    require_gcs(args.gcs_root, "--gcs-root")
    require_gcs(args.init_checkpoint, "--init-checkpoint")

    if args.output_dir is not None:
        args.output_dir = require_gcs(args.output_dir, "--output-dir")
    else:
        args.output_dir = join_gcs(args.gcs_root, "proc_data", "race")

    if args.model_dir is not None:
        args.model_dir = require_gcs(args.model_dir, "--model-dir")
    else:
        args.model_dir = join_gcs(args.gcs_root, "experiment", "race")

    if not args.tpu_name.strip():
        raise ValueError("--tpu-name must not be empty")

    for flag in args.extra_flag or []:
        if "\n" in flag or "\r" in flag:
            raise ValueError("--extra-flag values must not contain newlines")
        if not flag.startswith("--"):
            raise ValueError("--extra-flag values must be run_race.py flags beginning with --")

    if args.validate_local_paths:
        validate_existing_dir(args.race_dir, "--race-dir")
        validate_existing_file(args.model_config_path, "--model-config-path")
        validate_existing_file(args.spiece_model_file, "--spiece-model-file")


def add_flag(cmd, name, value):
    cmd.append("--{}={}".format(name, value))


def build_command(args):
    validate_args(args)

    cmd = [args.python, args.run_script]
    add_flag(cmd, "use_tpu", "True")
    add_flag(cmd, "tpu", args.tpu_name)
    if args.tpu_zone:
        add_flag(cmd, "tpu_zone", args.tpu_zone)
    if args.gcp_project:
        add_flag(cmd, "gcp_project", args.gcp_project)
    add_flag(cmd, "num_hosts", args.num_hosts)
    add_flag(cmd, "num_core_per_host", args.num_core_per_host)
    add_flag(cmd, "model_config_path", args.model_config_path)
    add_flag(cmd, "spiece_model_file", args.spiece_model_file)
    add_flag(cmd, "output_dir", args.output_dir)
    add_flag(cmd, "init_checkpoint", args.init_checkpoint)
    add_flag(cmd, "model_dir", args.model_dir)
    add_flag(cmd, "data_dir", args.race_dir)
    add_flag(cmd, "max_seq_length", args.max_seq_length)
    add_flag(cmd, "max_qa_length", args.max_qa_length)
    add_flag(cmd, "uncased", bool_text(args.uncased))
    add_flag(cmd, "do_train", bool_text(args.do_train))
    add_flag(cmd, "train_batch_size", args.train_batch_size)
    add_flag(cmd, "do_eval", bool_text(args.do_eval))
    add_flag(cmd, "eval_batch_size", args.eval_batch_size)
    add_flag(cmd, "eval_split", args.eval_split)
    if args.high_only:
        add_flag(cmd, "high_only", "True")
    if args.middle_only:
        add_flag(cmd, "middle_only", "True")
    if args.overwrite_data:
        add_flag(cmd, "overwrite_data", "True")
    add_flag(cmd, "train_steps", args.train_steps)
    add_flag(cmd, "save_steps", args.save_steps)
    add_flag(cmd, "iterations", args.iterations)
    add_flag(cmd, "warmup_steps", args.warmup_steps)
    add_flag(cmd, "learning_rate", args.learning_rate)
    add_flag(cmd, "weight_decay", args.weight_decay)
    add_flag(cmd, "adam_epsilon", args.adam_epsilon)

    for flag in args.extra_flag or []:
        cmd.append(flag)

    return cmd


def format_command(cmd, one_line=False):
    quoted = [shlex.quote(str(part)) for part in cmd]
    if one_line:
        return " ".join(quoted)
    return " \\\n  ".join(quoted)


def add_common_arguments(parser, profile_name):
    defaults = PROFILES[profile_name]
    parser.add_argument("--python", default="python", help="Python executable used in the printed command.")
    parser.add_argument("--run-script", default="run_race.py", help="run_race.py path or command used in the printed command.")
    parser.add_argument("--race-dir", required=True, help="Local unpacked RACE root containing train/dev/test and middle/high subdirectories.")
    parser.add_argument("--model-config-path", required=True, help="Local xlnet_config.json path from the released model archive.")
    parser.add_argument("--spiece-model-file", required=True, help="Local spiece.model path from the released model archive.")
    parser.add_argument("--init-checkpoint", required=True, help="TPU-readable checkpoint prefix, normally gs://.../xlnet_model.ckpt.")
    parser.add_argument("--gcs-root", required=True, help="GCS root used to derive default output/model directories.")
    parser.add_argument("--output-dir", help="GCS TFRecord cache directory. Default: <gcs-root>/proc_data/race.")
    parser.add_argument("--model-dir", help="GCS Estimator model directory. Default: <gcs-root>/experiment/race.")
    parser.add_argument("--tpu-name", required=True, help="Cloud TPU name for --tpu.")
    parser.add_argument("--tpu-zone", help="Optional Cloud TPU zone.")
    parser.add_argument("--gcp-project", help="Optional GCP project.")

    parser.add_argument("--num-hosts", type=positive_int, default=defaults["num_hosts"], help="Override --num_hosts.")
    parser.add_argument("--num-core-per-host", type=positive_int, default=defaults["num_core_per_host"], help="Override --num_core_per_host.")
    parser.add_argument("--train-batch-size", type=positive_int, default=defaults["train_batch_size"], help="Override --train_batch_size; one RACE example has four candidates.")
    parser.add_argument("--eval-batch-size", type=positive_int, default=defaults["eval_batch_size"], help="Override --eval_batch_size.")
    parser.add_argument("--max-seq-length", type=positive_int, default=512, help="Per-candidate max sequence length.")
    parser.add_argument("--max-qa-length", type=positive_int, default=128, help="Max tokenized question-answer length.")
    parser.add_argument("--eval-split", choices=["dev", "test"], default="dev", help="Evaluation split.")

    level = parser.add_mutually_exclusive_group()
    level.add_argument("--high-only", action="store_true", help="Add --high_only=True; skip middle examples.")
    level.add_argument("--middle-only", action="store_true", help="Add --middle_only=True; skip high examples.")

    phase = parser.add_mutually_exclusive_group()
    phase.add_argument("--train-only", action="store_true", help="Print a train-only command by setting --do_eval=False.")
    phase.add_argument("--eval-only", action="store_true", help="Print an eval-only command by setting --do_train=False.")
    parser.add_argument("--no-train", dest="do_train", action="store_false", default=True, help="Disable training.")
    parser.add_argument("--no-eval", dest="do_eval", action="store_false", default=True, help="Disable evaluation.")

    parser.add_argument("--uncased", action="store_true", help="Emit --uncased=True. Default is the cased recipe.")
    parser.add_argument("--overwrite-data", action="store_true", help="Emit --overwrite_data=True.")
    parser.add_argument("--train-steps", type=positive_int, default=12000, help="Training steps.")
    parser.add_argument("--save-steps", type=positive_int, default=1000, help="Checkpoint save interval.")
    parser.add_argument("--iterations", type=positive_int, default=1000, help="TPU loop iterations.")
    parser.add_argument("--warmup-steps", type=nonnegative_int, default=1000, help="Warmup steps.")
    parser.add_argument("--learning-rate", type=number, default="2e-5", help="Learning rate.")
    parser.add_argument("--weight-decay", type=number, default="0", help="Weight decay.")
    parser.add_argument("--adam-epsilon", type=number, default="1e-6", help="Adam epsilon.")
    parser.add_argument("--extra-flag", action="append", help="Append one raw run_race.py flag beginning with --. Repeat as needed.")
    parser.add_argument("--validate-local-paths", action="store_true", help="Check local RACE/config/SentencePiece paths before printing.")
    parser.add_argument("--one-line", action="store_true", help="Print one shell line instead of backslash-wrapped output.")


def make_parser():
    parser = argparse.ArgumentParser(
        description="Print dry XLNet RACE run_race.py commands adapted from the TPU templates."
    )
    subparsers = parser.add_subparsers(dest="profile")
    # Python 3.7 supports required subparsers, but set it defensively for help readability.
    subparsers.required = True

    for profile_name, data in sorted(PROFILES.items()):
        subparser = subparsers.add_parser(profile_name, help=data["help"], description=data["help"])
        subparser.set_defaults(profile=profile_name)
        add_common_arguments(subparser, profile_name)

    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.train_only:
        args.do_eval = False
    if args.eval_only:
        args.do_train = False

    try:
        cmd = build_command(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    print(format_command(cmd, one_line=args.one_line))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Print dry timm reference-script commands.

This helper intentionally does not import timm, inspect devices, open datasets, or
check that script paths exist. It only assembles shell-quoted commands that a user
can review, copy, and adapt.
"""
import argparse
import shlex
import sys
from typing import Iterable, List, Optional, Sequence


DEFAULT_SCRIPTS = {
    "train": "train.py",
    "validate": "validate.py",
    "inference": "inference.py",
}


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", required=True, help="Dataset root or split folder to pass as --data-dir.")
    parser.add_argument("--model", required=True, help="timm model name to pass as --model.")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size to pass as --batch-size.")
    parser.add_argument("--device", default=None, help="Device string such as cuda, cuda:0, cpu, mps, or npu.")
    parser.add_argument("--pretrained", action="store_true", help="Add --pretrained.")
    parser.add_argument("--checkpoint", default=None, help="Checkpoint path for validate.py or inference.py.")
    parser.add_argument("--amp", action="store_true", help="Add --amp for native PyTorch autocast.")
    parser.add_argument("--workers", type=int, default=None, help="Data-loader worker count to pass as --workers.")
    parser.add_argument(
        "--script-path",
        default=None,
        help="Override script path. Defaults to train.py, validate.py, or inference.py for the selected mode.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Append one raw argument token. Use --extra-arg=--flag for values beginning with '-'.",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable used for non-distributed commands (default: python).",
    )


def _extend_option(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def _extend_bool(command: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def _extend_extra(command: List[str], extra_args: Iterable[str]) -> None:
    command.extend(str(arg) for arg in extra_args)


def build_command(args: argparse.Namespace) -> List[str]:
    script_path = args.script_path or DEFAULT_SCRIPTS[args.mode]
    command = [args.python, script_path]

    _extend_option(command, "--data-dir", args.data_dir)
    _extend_option(command, "--model", args.model)
    _extend_option(command, "--batch-size", args.batch_size)
    _extend_option(command, "--device", args.device)
    _extend_option(command, "--workers", args.workers)
    _extend_bool(command, "--pretrained", args.pretrained)
    _extend_bool(command, "--amp", args.amp)

    if args.mode in ("validate", "inference"):
        _extend_option(command, "--checkpoint", args.checkpoint)
    elif args.checkpoint:
        command.extend(["--initial-checkpoint", args.checkpoint])

    if args.mode == "validate":
        _extend_option(command, "--results-file", args.results_file)
        _extend_option(command, "--results-format", args.results_format)
        _extend_bool(command, "--retry", args.retry)
    elif args.mode == "inference":
        _extend_option(command, "--results-dir", args.results_dir)
        _extend_option(command, "--results-file", args.results_file)
        if args.results_format:
            command.append("--results-format")
            command.extend(args.results_format)
        _extend_option(command, "--topk", args.topk)
        _extend_bool(command, "--include-index", args.include_index)
        _extend_bool(command, "--no-console-results", args.no_console_results)
    else:
        _extend_option(command, "--output", args.output)
        _extend_option(command, "--experiment", args.experiment)
        _extend_option(command, "--config", args.config)

    _extend_extra(command, args.extra_arg)
    return command


def render_command(command: Sequence[str]) -> str:
    return shlex.join(command)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build dry shell commands for timm train.py, validate.py, and inference.py.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    train = subparsers.add_parser("train", help="Print a train.py command.")
    _add_common_args(train)
    train.add_argument("--output", default=None, help="Training output folder.")
    train.add_argument("--experiment", default=None, help="Training experiment subfolder name.")
    train.add_argument("--config", default=None, help="YAML config file consumed by train.py.")

    validate = subparsers.add_parser("validate", help="Print a validate.py command.")
    _add_common_args(validate)
    validate.add_argument("--results-file", default=None, help="Validation results CSV/JSON path.")
    validate.add_argument("--results-format", choices=("csv", "json"), default=None, help="Validation results format.")
    validate.add_argument("--retry", action="store_true", help="Add validate.py --retry for batch-size decay retries.")

    inference = subparsers.add_parser("inference", help="Print an inference.py command.")
    _add_common_args(inference)
    inference.add_argument("--results-dir", default=None, help="Inference results directory.")
    inference.add_argument("--results-file", default=None, help="Inference results filename stem.")
    inference.add_argument(
        "--results-format",
        nargs="+",
        choices=("csv", "json", "json-split", "parquet"),
        default=None,
        help="One or more inference result formats.",
    )
    inference.add_argument("--topk", type=int, default=None, help="Top-k predictions to output.")
    inference.add_argument("--include-index", action="store_true", help="Include class index columns in inference output.")
    inference.add_argument("--no-console-results", action="store_true", help="Suppress console result JSON.")

    return parser


def _split_passthrough(argv: Optional[Sequence[str]]) -> tuple[Optional[Sequence[str]], List[str]]:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    if "--" not in argv:
        return argv, []
    separator = argv.index("--")
    return argv[:separator], argv[separator + 1:]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    parser_args, passthrough_args = _split_passthrough(argv)
    args = parser.parse_args(parser_args)
    args.extra_arg.extend(passthrough_args)
    print(render_command(build_command(args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

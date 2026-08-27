#!/usr/bin/env python3
"""Dry-run composer for BEVFormer distributed evaluation commands."""

from __future__ import annotations

import argparse
import shlex

DEFAULT_EVAL_PORT = 29503


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formats the error
        raise argparse.ArgumentTypeError("expected an integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a BEVFormer distributed evaluation command"
    )
    parser.add_argument("--config", required=True, help="evaluation config path")
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="checkpoint path required for evaluation",
    )
    parser.add_argument(
        "--gpus",
        type=positive_int,
        default=1,
        help="number of GPUs for the distributed launcher",
    )
    parser.add_argument(
        "--port",
        type=positive_int,
        default=DEFAULT_EVAL_PORT,
        help="master port for torch.distributed.launch",
    )
    parser.add_argument(
        "--eval",
        nargs="+",
        metavar="METRIC",
        help="evaluation metrics such as bbox",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="format results without evaluating",
    )
    parser.add_argument(
        "--show", action="store_true", help="show the predictions"
    )
    parser.add_argument(
        "--show-dir",
        help="directory for visual outputs",
    )
    parser.add_argument(
        "--out",
        help="pickle file for raw outputs",
    )
    parser.add_argument(
        "--gpu-collect",
        action="store_true",
        help="collect results on GPU",
    )
    parser.add_argument(
        "--tmpdir",
        help="temporary directory for CPU collection",
    )
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        metavar="KEY=VALUE",
        help="OpenMMLab config overrides",
    )
    parser.add_argument(
        "--eval-options",
        nargs="+",
        metavar="KEY=VALUE",
        help="extra kwargs forwarded to dataset.evaluate()",
    )
    args = parser.parse_args()

    if args.eval and args.format_only:
        parser.error("--eval and --format-only cannot be used together")
    if args.out and not args.out.endswith((".pkl", ".pickle")):
        parser.error("--out must end in .pkl or .pickle")

    return args


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.port}",
        "tools/test.py",
        args.config,
        args.checkpoint,
        "--launcher",
        "pytorch",
    ]

    if args.eval:
        command.append("--eval")
        command.extend(args.eval)
    elif not any([args.format_only, args.show, args.show_dir, args.out]):
        command.extend(["--eval", "bbox"])

    if args.format_only:
        command.append("--format-only")
    if args.show:
        command.append("--show")
    if args.show_dir:
        command.extend(["--show-dir", args.show_dir])
    if args.out:
        command.extend(["--out", args.out])
    if args.gpu_collect:
        command.append("--gpu-collect")
    if args.tmpdir:
        command.extend(["--tmpdir", args.tmpdir])
    if args.cfg_options:
        command.append("--cfg-options")
        command.extend(args.cfg_options)
    if args.eval_options:
        command.append("--eval-options")
        command.extend(args.eval_options)

    return command


def main() -> None:
    args = parse_args()
    print(shlex.join(build_command(args)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build safe Detectron2 train/eval commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List


def _split_override(text: str, style: str) -> List[str]:
    if style == "yacs":
        if "=" in text:
            key, value = text.split("=", 1)
            return [key, value]
        parts = text.strip().split(None, 1)
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                "Yacs overrides must be 'KEY VALUE' or KEY=VALUE; got: {}".format(text)
            )
        return parts
    if "=" not in text:
        raise argparse.ArgumentTypeError(
            "LazyConfig overrides must use path.key=value syntax; got: {}".format(text)
        )
    return [text]


def _quote_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def build_command(args: argparse.Namespace) -> List[str]:
    script = args.script
    if script is None:
        script = "PROJECT_LAZY_TRAIN_DRIVER.py" if args.style == "lazy" else "PROJECT_TRAIN_DRIVER.py"

    command: List[str] = [args.python, script, "--config-file", args.config_file]

    if args.num_gpus is not None:
        command.extend(["--num-gpus", str(args.num_gpus)])
    if args.num_machines is not None:
        command.extend(["--num-machines", str(args.num_machines)])
    if args.machine_rank is not None:
        command.extend(["--machine-rank", str(args.machine_rank)])
    if args.dist_url:
        command.extend(["--dist-url", args.dist_url])
    if args.resume:
        command.append("--resume")
    if args.eval_only:
        command.append("--eval-only")

    for override in args.override:
        command.extend(_split_override(override, args.style))
    return command


def infer_warnings(args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    config_suffix = Path(args.config_file).suffix.lower()
    if args.style == "yacs" and config_suffix == ".py":
        warnings.append("Yacs style was selected for a .py config; LazyConfig may be intended.")
    if args.style == "lazy" and config_suffix in {".yaml", ".yml"}:
        warnings.append("LazyConfig style was selected for a YAML config; Yacs may be intended.")
    if args.eval_only and args.resume:
        warnings.append("--eval-only --resume may load OUTPUT_DIR/last_checkpoint instead of the explicit weights field.")
    if args.num_gpus and args.num_gpus > 1:
        warnings.append("Multi-GPU commands can be expensive; get user approval before running.")
    if args.num_machines and args.num_machines > 1:
        warnings.append("Multi-machine commands require matching dist-url, machine ranks, and network reachability.")
    if not args.override:
        warnings.append("No config overrides were provided; verify weights, datasets, output dir, LR, and batch size separately.")
    return warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a Detectron2 training/evaluation command without executing it."
    )
    parser.add_argument("--style", choices=["yacs", "lazy"], required=True, help="Config system.")
    parser.add_argument("--config-file", required=True, help="Config file to pass to Detectron2.")
    parser.add_argument("--python", default="python", help="Python executable placeholder to print.")
    parser.add_argument(
        "--script",
        help=(
            "Project-local train/eval driver to print. Defaults to a placeholder; "
            "replace it with your own driver that follows Detectron2's standard parser shape."
        ),
    )
    parser.add_argument("--num-gpus", type=int, default=1, help="GPUs per machine.")
    parser.add_argument("--num-machines", type=int, help="Total machine count.")
    parser.add_argument("--machine-rank", type=int, help="Rank of this machine.")
    parser.add_argument("--dist-url", help="Distributed initialization URL.")
    parser.add_argument("--resume", action="store_true", help="Include --resume.")
    parser.add_argument("--eval-only", action="store_true", help="Include --eval-only.")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help=(
            "Config override. Repeat as needed. "
            "Yacs accepts 'KEY VALUE' or KEY=VALUE; LazyConfig requires path.key=value."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = build_command(args)
    print("Command preview (not executed):")
    print(_quote_join(command))
    warnings = infer_warnings(args)
    if warnings:
        print("\nReview before running:")
        for item in warnings:
            print(f"- {item}")
    print(
        "\nSafety: this helper only prints a command; it does not import detectron2, "
        "depend on the original source checkout, or start training."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

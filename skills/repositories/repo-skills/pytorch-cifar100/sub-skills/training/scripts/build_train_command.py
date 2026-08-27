#!/usr/bin/env python3
"""Build and validate a train.py command for the pytorch-cifar100 training workflow.

This helper is self-contained. It does not import the repository or launch training.
Use --list-nets to inspect the supported net keys and --json for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import List

SUPPORTED_NETS: List[str] = [
    "vgg16",
    "vgg13",
    "vgg11",
    "vgg19",
    "densenet121",
    "densenet161",
    "densenet169",
    "densenet201",
    "googlenet",
    "inceptionv3",
    "inceptionv4",
    "inceptionresnetv2",
    "xception",
    "resnet18",
    "resnet34",
    "resnet50",
    "resnet101",
    "resnet152",
    "preactresnet18",
    "preactresnet34",
    "preactresnet50",
    "preactresnet101",
    "preactresnet152",
    "resnext50",
    "resnext101",
    "resnext152",
    "shufflenet",
    "shufflenetv2",
    "squeezenet",
    "mobilenet",
    "mobilenetv2",
    "nasnet",
    "attention56",
    "attention92",
    "seresnet18",
    "seresnet34",
    "seresnet50",
    "seresnet101",
    "seresnet152",
    "wideresnet",
    "stochasticdepth18",
    "stochasticdepth34",
    "stochasticdepth50",
    "stochasticdepth101",
]

DEFAULT_PYTHON = "python"
DEFAULT_BATCH_SIZE = 128
DEFAULT_LR = 0.1
DEFAULT_WARM = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a validated train.py command without running training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--net", help="network key passed to train.py -net")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="value for train.py -b")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR, help="value for train.py -lr")
    parser.add_argument("--warm", type=int, default=DEFAULT_WARM, help="value for train.py -warm")
    parser.add_argument("--gpu", action="store_true", help="add train.py -gpu")
    parser.add_argument("--resume", action="store_true", help="add train.py -resume")
    parser.add_argument("--python", default=DEFAULT_PYTHON, help="python command to place before train.py")
    parser.add_argument(
        "--repo-root-placeholder",
        default="<repo-root>",
        help="label used in explanatory output to indicate where to run the command",
    )
    parser.add_argument("--explain", action="store_true", help="print a fuller human-readable explanation")
    parser.add_argument("--json", action="store_true", help="print JSON instead of plain text")
    parser.add_argument("--list-nets", action="store_true", help="list the supported network keys and exit")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.list_nets:
        return
    if not args.net:
        raise SystemExit("--net is required unless --list-nets is set")
    if args.net not in SUPPORTED_NETS:
        supported = ", ".join(SUPPORTED_NETS)
        raise SystemExit(f"unsupported net: {args.net}\nSupported keys: {supported}")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be greater than zero")
    if args.lr <= 0:
        raise SystemExit("--lr must be greater than zero")
    if args.warm < 0:
        raise SystemExit("--warm must be zero or greater")
    if not str(args.python).strip():
        raise SystemExit("--python must not be empty")
    if not str(args.repo_root_placeholder).strip():
        raise SystemExit("--repo-root-placeholder must not be empty")


def build_command(args: argparse.Namespace) -> str:
    parts = [shlex.quote(str(args.python)), "train.py", "-net", shlex.quote(args.net)]
    if args.gpu:
        parts.append("-gpu")
    parts.extend(["-b", str(args.batch_size), "-warm", str(args.warm), "-lr", format(args.lr, "g")])
    if args.resume:
        parts.append("-resume")
    return " ".join(parts)


def build_warnings(args: argparse.Namespace) -> List[str]:
    warnings = [
        "train.py will download CIFAR-100 into ./data when the dataset is missing.",
        "A full training run is long-running: 200 epochs, warmup on early epochs, MultiStepLR at 60/120/160, and checkpoint output under checkpoint/<net>/<timestamp>/.",
        "TensorBoard logs are written under runs/<net>/<TIME_NOW>/ and the log folder is timestamped at launch.",
    ]
    if args.gpu:
        warnings.append(
            "GPU mode requested; confirm a CUDA-capable PyTorch runtime and enough device memory before launching."
        )
    if args.resume:
        warnings.append(
            "Resume mode searches the most recent non-empty checkpoint folder for the selected net and raises if it cannot find usable weights."
        )
    return warnings


def build_explanation(args: argparse.Namespace, command: str, warnings: List[str]) -> List[str]:
    lines = [
        f"Repo root placeholder: {args.repo_root_placeholder}",
        f"Command: {command}",
        "",
        "Notes:",
        "- This helper prints a command only; it never launches training.",
        f"- train.py defaults used here: batch size {DEFAULT_BATCH_SIZE}, warmup {DEFAULT_WARM}, lr {DEFAULT_LR}.",
        "- The command builder validates the exact network key before printing the command.",
        "",
        "Warnings:",
    ]
    lines.extend(f"- {warning}" for warning in warnings)
    return lines


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_nets:
        if args.json:
            print(json.dumps({"supported_nets": SUPPORTED_NETS, "count": len(SUPPORTED_NETS)}, indent=2))
        else:
            print("\n".join(SUPPORTED_NETS))
        return 0

    validate_args(args)
    command = build_command(args)
    warnings = build_warnings(args)

    if args.json:
        payload = {
            "repo_root_placeholder": args.repo_root_placeholder,
            "command": command,
            "warnings": warnings,
            "supported_nets_count": len(SUPPORTED_NETS),
            "supported_nets": SUPPORTED_NETS,
            "defaults": {
                "batch_size": DEFAULT_BATCH_SIZE,
                "lr": DEFAULT_LR,
                "warm": DEFAULT_WARM,
                "gpu": False,
                "resume": False,
                "python": DEFAULT_PYTHON,
            },
        }
        if args.explain:
            payload["explanation"] = build_explanation(args, command, warnings)
        print(json.dumps(payload, indent=2))
        return 0

    if args.explain:
        print("\n".join(build_explanation(args, command, warnings)))
    else:
        print(command)
        print("")
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build prerequisite-aware native DARTS commands without running training.

This helper is self-contained and safe: it prints commands and notes for the
legacy quark0/darts scripts, but never imports the original repo, downloads
files, or launches a training/evaluation job.

Examples:
  python darts_command_builder.py list
  python darts_command_builder.py build cnn-search --smoke --gpu 0
  python darts_command_builder.py build rnn-train-wt2 --data ../data/wikitext-2
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Workflow:
    key: str
    title: str
    subdir: str
    script: str
    description: str
    default_args: List[str]
    smoke_args: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    expected_signal: str = ""


WORKFLOWS: Dict[str, Workflow] = {
    "cnn-search": Workflow(
        key="cnn-search",
        title="CNN CIFAR-10 architecture search",
        subdir="cnn",
        script="train_search.py",
        description="Search convolutional normal/reduction cells on CIFAR-10.",
        default_args=["--unrolled"],
        smoke_args=["--epochs", "1", "--batch_size", "8", "--train_portion", "0.1", "--report_freq", "1", "--save", "smoke"],
        prerequisites=["legacy Python/PyTorch 0.3.1/torchvision 0.2.0", "CUDA GPU", "CIFAR-10 root; torchvision may download data"],
        expected_signal="search-*/log.txt, logged genotype, train_acc/valid_acc, weights.pt",
    ),
    "cnn-train": Workflow(
        key="cnn-train",
        title="CNN CIFAR-10 fixed-genotype training",
        subdir="cnn",
        script="train.py",
        description="Train/evaluate a fixed CNN genotype on CIFAR-10.",
        default_args=["--auxiliary", "--cutout"],
        smoke_args=["--epochs", "1", "--batch_size", "8", "--init_channels", "8", "--layers", "4", "--save", "smoke", "--report_freq", "1"],
        prerequisites=["legacy Python/PyTorch 0.3.1/torchvision 0.2.0", "CUDA GPU", "CIFAR-10 root; torchvision may download data"],
        expected_signal="eval-*/log.txt, train_acc/valid_acc, weights.pt",
    ),
    "cnn-test": Workflow(
        key="cnn-test",
        title="CNN CIFAR-10 pretrained checkpoint evaluation",
        subdir="cnn",
        script="test.py",
        description="Evaluate a raw-state-dict CIFAR-10 checkpoint.",
        default_args=["--auxiliary", "--model_path", "cifar10_model.pt"],
        smoke_args=[],
        prerequisites=["legacy Python/PyTorch 0.3.1/torchvision 0.2.0", "CUDA GPU", "CIFAR-10 data", "raw model state dict matching arch/channels/layers/auxiliary"],
        expected_signal="test_acc log; README reports about 97.37% accuracy for the published checkpoint",
    ),
    "cnn-imagenet-train": Workflow(
        key="cnn-imagenet-train",
        title="CNN ImageNet fixed-genotype training",
        subdir="cnn",
        script="train_imagenet.py",
        description="Train a fixed CNN genotype on ImageNet ImageFolder train/val folders.",
        default_args=["--auxiliary"],
        smoke_args=["--epochs", "1", "--batch_size", "4", "--init_channels", "8", "--layers", "2", "--save", "smoke", "--report_freq", "1"],
        prerequisites=["legacy Python/PyTorch 0.3.1/torchvision 0.2.0", "CUDA GPU", "ImageNet-style train/val class folders"],
        expected_signal="eval-*/checkpoint.pth.tar, model_best.pth.tar, valid_acc_top1/top5",
    ),
    "cnn-imagenet-test": Workflow(
        key="cnn-imagenet-test",
        title="CNN ImageNet pretrained checkpoint evaluation",
        subdir="cnn",
        script="test_imagenet.py",
        description="Evaluate an ImageNet checkpoint dictionary containing state_dict.",
        default_args=["--auxiliary", "--model_path", "imagenet_model.pt"],
        smoke_args=[],
        prerequisites=["legacy Python/PyTorch 0.3.1/torchvision 0.2.0", "CUDA GPU", "ImageNet val class folders", "checkpoint dict with state_dict"],
        expected_signal="valid_acc_top1/top5; README reports about 73.3% top-1 and 91.3% top-5 accuracy",
    ),
    "rnn-search": Workflow(
        key="rnn-search",
        title="RNN PTB architecture search",
        subdir="rnn",
        script="train_search.py",
        description="Search a recurrent DARTS cell on Penn Treebank.",
        default_args=["--unrolled"],
        smoke_args=["--epochs", "1", "--batch_size", "8", "--small_batch_size", "8", "--emsize", "32", "--nhid", "32", "--nhidlast", "32", "--save", "smoke", "--log-interval", "1"],
        prerequisites=["legacy PyTorch", "CUDA recommended/expected by default", "PTB train.txt/valid.txt/test.txt"],
        expected_signal="search-*/log.txt, logged recurrent genotype, validation perplexity, model.pt/optimizer.pt/misc.pt",
    ),
    "rnn-train-ptb": Workflow(
        key="rnn-train-ptb",
        title="RNN PTB fixed-genotype training",
        subdir="rnn",
        script="train.py",
        description="Train/evaluate the fixed recurrent DARTS genotype on PTB.",
        default_args=[],
        smoke_args=["--epochs", "1", "--batch_size", "8", "--small_batch_size", "8", "--emsize", "32", "--nhid", "32", "--nhidlast", "32", "--save", "smoke", "--log-interval", "1"],
        prerequisites=["legacy PyTorch", "CUDA path expected by default", "PTB train.txt/valid.txt/test.txt"],
        expected_signal="eval-*/log.txt, validation perplexity, final test perplexity, model.pt/optimizer.pt/misc.pt",
    ),
    "rnn-train-wt2": Workflow(
        key="rnn-train-wt2",
        title="RNN WikiText-2 fixed-genotype training",
        subdir="rnn",
        script="train.py",
        description="Train/evaluate the fixed recurrent DARTS genotype on WikiText-2 using README hyperparameters.",
        default_args=["--data", "../data/wikitext-2", "--dropouth", "0.15", "--emsize", "700", "--nhidlast", "700", "--nhid", "700", "--wdecay", "5e-7"],
        smoke_args=["--data", "../data/wikitext-2", "--epochs", "1", "--batch_size", "8", "--small_batch_size", "8", "--emsize", "32", "--nhid", "32", "--nhidlast", "32", "--save", "smoke", "--log-interval", "1"],
        prerequisites=["legacy PyTorch", "CUDA path expected by default", "WikiText-2 train.txt/valid.txt/test.txt"],
        expected_signal="eval-*/log.txt, validation/test perplexity, checkpoint trio",
    ),
    "rnn-test": Workflow(
        key="rnn-test",
        title="RNN PTB pretrained checkpoint evaluation",
        subdir="rnn",
        script="test.py",
        description="Evaluate a serialized PTB model checkpoint.",
        default_args=["--model_path", "ptb_model.pt"],
        smoke_args=[],
        prerequisites=["legacy PyTorch", "CUDA path expected by test.py", "PTB data", "serialized model object checkpoint"],
        expected_signal="test perplexity; README reports 55.68 for the published checkpoint",
    ),
}


def quote_command(parts: List[str]) -> str:
    shell_tokens = {"&&", "||", "|", ";"}
    return " ".join(part if part in shell_tokens else shlex.quote(part) for part in parts)


def merge_args(base: List[str], overrides: argparse.Namespace, workflow: Workflow) -> List[str]:
    args = list(base)
    if overrides.data:
        # Remove the first existing --data pair if present.
        cleaned: List[str] = []
        skip = False
        for idx, item in enumerate(args):
            if skip:
                skip = False
                continue
            if item == "--data" and idx + 1 < len(args):
                skip = True
                continue
            cleaned.append(item)
        args = cleaned + ["--data", overrides.data]
    elif workflow.key.startswith("cnn-imagenet") and "--data" not in args:
        args += ["--data", "../data/imagenet/"]
    elif workflow.key.startswith("cnn") and "--data" not in args:
        args += ["--data", "../data"]
    elif workflow.key.startswith("rnn") and "--data" not in args:
        args += ["--data", "../data/penn/"]

    if overrides.arch and workflow.key.startswith("cnn") and workflow.key != "cnn-search":
        args += ["--arch", overrides.arch]
    if overrides.gpu is not None:
        args += ["--gpu", str(overrides.gpu)]
    if overrides.model_path:
        # Override/add --model_path.
        cleaned = []
        skip = False
        for idx, item in enumerate(args):
            if skip:
                skip = False
                continue
            if item == "--model_path" and idx + 1 < len(args):
                skip = True
                continue
            cleaned.append(item)
        args = cleaned + ["--model_path", overrides.model_path]
    if overrides.save:
        args += ["--save", overrides.save]
    if overrides.extra:
        args += overrides.extra
    return args


def build_command(workflow: Workflow, ns: argparse.Namespace) -> Dict[str, object]:
    selected_args = workflow.smoke_args if ns.smoke else workflow.default_args
    args = merge_args(selected_args, ns, workflow)
    command = ["cd", workflow.subdir, "&&", "python", workflow.script] + args
    return {
        "workflow": workflow.key,
        "title": workflow.title,
        "description": workflow.description,
        "native_command": quote_command(command),
        "smoke_mode": bool(ns.smoke),
        "prerequisites": workflow.prerequisites,
        "expected_signal": workflow.expected_signal,
        "notes": [
            "This helper does not run the command.",
            "Run native DARTS scripts only in a compatible legacy runtime; modern Python/PyTorch usually needs a port.",
            "Do not report smoke-mode output as paper accuracy or perplexity.",
        ],
    }


def cmd_list(_ns: argparse.Namespace) -> int:
    for wf in WORKFLOWS.values():
        print(f"{wf.key}\t{wf.title}")
    return 0


def cmd_build(ns: argparse.Namespace) -> int:
    workflow = WORKFLOWS[ns.workflow]
    payload = build_command(workflow, ns)
    if ns.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["title"])
        print("Command:")
        print("  " + payload["native_command"])
        print("Prerequisites:")
        for item in payload["prerequisites"]:
            print("  - " + item)
        print("Expected signal:")
        print("  " + payload["expected_signal"])
        print("Notes:")
        for item in payload["notes"]:
            print("  - " + item)
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build safe, prerequisite-aware DARTS native commands without running them.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List known workflow ids.")
    p_list.set_defaults(func=cmd_list)

    p_build = sub.add_parser("build", help="Print a native command and prerequisites for one workflow.")
    p_build.add_argument("workflow", choices=sorted(WORKFLOWS), help="Workflow id from the list command.")
    p_build.add_argument("--smoke", action="store_true", help="Use a tiny wiring-check variant when one is defined.")
    p_build.add_argument("--data", help="Override the dataset root passed to --data.")
    p_build.add_argument("--arch", default="DARTS", help="CNN architecture name for CNN workflows; default DARTS.")
    p_build.add_argument("--gpu", type=int, help="GPU id to pass to native scripts.")
    p_build.add_argument("--model-path", help="Override the checkpoint/model path for test workflows.")
    p_build.add_argument("--save", help="Append a --save value.")
    p_build.add_argument("--extra", nargs=argparse.REMAINDER, help="Append extra native script arguments after --extra.")
    p_build.add_argument("--json", action="store_true", help="Emit JSON instead of prose.")
    p_build.set_defaults(func=cmd_build)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())

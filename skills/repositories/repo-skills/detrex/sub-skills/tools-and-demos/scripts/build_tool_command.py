#!/usr/bin/env python3
"""Build safe detrex tool commands without executing them.

The helper prints a shell command or a JSON plan. It never downloads weights,
scans datasets, or runs benchmarks.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MODULES = {
    "demo": "demo.demo",
    "analyze": "tools.analyze_model",
    "visualize-data": "tools.visualize_data",
    "visualize-json": "tools.visualize_json_results",
    "benchmark": "tools.benchmark",
}


@dataclass
class CommandPlan:
    workflow: str
    command: str
    warnings: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "workflow": self.workflow,
            "command": self.command,
            "warnings": self.warnings,
        }


def shell_quote(tokens: Sequence[object]) -> str:
    return " ".join(shlex.quote(str(token)) for token in tokens)


def add_checkpoint_override(overrides: list[str], checkpoint: str | None) -> list[str]:
    merged = list(overrides)
    if checkpoint and not any(item.startswith("train.init_checkpoint=") for item in merged):
        merged = [f"train.init_checkpoint={checkpoint}"] + merged
    return merged


def build_demo_plan(args: argparse.Namespace, parser: argparse.ArgumentParser) -> CommandPlan:
    tokens: list[object] = ["python", "-m", MODULES["demo"], "--config-file", args.config_file]
    warnings: list[str] = []

    if args.input:
        tokens.extend(["--input", *args.input])
        if len(args.input) > 1:
            if not args.output:
                warnings.append(
                    "Multiple image inputs without --output will open a window for each result."
                )
            elif not Path(args.output).is_dir():
                parser.error(
                    "Multiple image inputs require an existing output directory because the source demo only treats existing directories as directories."
                )
    elif args.video_input:
        tokens.extend(["--video-input", args.video_input])
        if not args.output:
            warnings.append("Video demo will open a window unless you add --output.")
    elif args.webcam:
        tokens.append("--webcam")
        if args.output:
            parser.error("--output is not supported with --webcam.")

    if args.output:
        tokens.extend(["--output", args.output])

    tokens.extend(
        [
            "--min_size_test",
            str(args.min_size_test),
            "--max_size_test",
            str(args.max_size_test),
            "--img_format",
            args.img_format,
            "--metadata_dataset",
            args.metadata_dataset,
            "--confidence-threshold",
            str(args.confidence_threshold),
        ]
    )

    checkpoint_present = bool(args.checkpoint) or any(
        item.startswith("train.init_checkpoint=") for item in args.override
    )
    overrides = add_checkpoint_override(list(args.override), args.checkpoint)
    if not checkpoint_present:
        warnings.append(
            "This demo usually loads cfg.train.init_checkpoint; add --checkpoint or an override if the config does not define one."
        )
    if overrides:
        tokens.extend(["--opts", *overrides])

    return CommandPlan("demo", shell_quote(tokens), warnings)


def build_analyze_plan(args: argparse.Namespace) -> CommandPlan:
    tokens: list[object] = [
        "python",
        "-m",
        MODULES["analyze"],
        "--tasks",
        *args.tasks,
        "--config-file",
        args.config_file,
        "--num-inputs",
        str(args.num_inputs),
    ]
    warnings: list[str] = []

    checkpoint_present = bool(args.checkpoint) or any(
        item.startswith("train.init_checkpoint=") for item in args.override
    )
    overrides = add_checkpoint_override(list(args.override), args.checkpoint)
    needs_checkpoint = any(task in {"flop", "activation"} for task in args.tasks)
    if needs_checkpoint and not checkpoint_present:
        warnings.append(
            "FLOP and activation analysis usually need a checkpoint and a test dataloader; add --checkpoint or an override."
        )
    if not needs_checkpoint and checkpoint_present:
        warnings.append("Parameter and structure analysis do not read the checkpoint override.")
    if overrides:
        tokens.extend(overrides)

    return CommandPlan("analyze", shell_quote(tokens), warnings)


def build_visualize_data_plan(args: argparse.Namespace) -> CommandPlan:
    tokens: list[object] = [
        "python",
        "-m",
        MODULES["visualize-data"],
        "--source",
        args.source,
        "--config-file",
        args.config_file,
        "--output-dir",
        args.output_dir,
    ]
    warnings: list[str] = []

    if args.show:
        tokens.append("--show")
    if args.source == "dataloader":
        warnings.append("The dataloader source can be effectively infinite; interrupt it manually after enough samples.")

    overrides = list(args.override)
    if overrides:
        tokens.extend(overrides)

    return CommandPlan("visualize-data", shell_quote(tokens), warnings)


def build_visualize_json_plan(args: argparse.Namespace) -> CommandPlan:
    tokens: list[object] = [
        "python",
        "-m",
        MODULES["visualize-json"],
        "--input",
        args.input,
        "--output",
        args.output,
        "--dataset",
        args.dataset,
        "--conf-threshold",
        str(args.conf_threshold),
    ]
    return CommandPlan("visualize-json", shell_quote(tokens), [])


def build_benchmark_plan(args: argparse.Namespace, parser: argparse.ArgumentParser) -> CommandPlan:
    if args.task == "eval" and (args.num_gpus != 1 or args.num_machines != 1):
        parser.error("tools.benchmark eval is single-GPU and single-node only; keep --num-gpus 1 --num-machines 1.")

    tokens: list[object] = [
        "python",
        "-m",
        MODULES["benchmark"],
        "--task",
        args.task,
        "--config-file",
        args.config_file,
        "--num-gpus",
        str(args.num_gpus),
        "--num-machines",
        str(args.num_machines),
        "--machine-rank",
        str(args.machine_rank),
        "--dist-url",
        args.dist_url,
    ]
    warnings: list[str] = []

    checkpoint_present = bool(args.checkpoint) or any(
        item.startswith("train.init_checkpoint=") for item in args.override
    )
    overrides = add_checkpoint_override(list(args.override), args.checkpoint)
    if args.task in {"train", "eval"} and not checkpoint_present:
        warnings.append(
            "Train and eval benchmarks usually need a checkpoint or a model-weight setting in the config."
        )
    if overrides:
        tokens.extend(overrides)

    warnings.append("The helper prints the benchmark command only; actual execution can be expensive.")
    if args.task == "data" or args.task == "data_advanced":
        warnings.append("Data benchmarks may require psutil at import time.")

    return CommandPlan("benchmark", shell_quote(tokens), warnings)


def build_parser() -> argparse.ArgumentParser:
    format_parent = argparse.ArgumentParser(add_help=False)
    format_parent.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="print the command as a shell string or JSON",
    )

    parser = argparse.ArgumentParser(
        description="Build a safe detrex tool command without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[format_parent],
    )

    subparsers = parser.add_subparsers(dest="workflow", required=True)

    demo = subparsers.add_parser(
        "demo",
        parents=[format_parent],
        help="build a generic image/video/webcam demo command",
    )
    demo_input = demo.add_mutually_exclusive_group(required=True)
    demo_input.add_argument(
        "--input",
        nargs="+",
        metavar="PATH",
        help="one image, many images, or a single glob pattern",
    )
    demo_input.add_argument("--video-input", metavar="FILE", help="a video file for demo visualization")
    demo_input.add_argument("--webcam", action="store_true", help="build a webcam command")
    demo.add_argument("--config-file", required=True, metavar="FILE", help="lazy config file")
    demo.add_argument("--output", metavar="PATH", help="output file or directory")
    demo.add_argument("--checkpoint", metavar="FILE", help="checkpoint to map to train.init_checkpoint")
    demo.add_argument("--min-size-test", type=int, default=800, help="smallest test-side resize")
    demo.add_argument("--max-size-test", type=int, default=1333, help="largest test-side resize")
    demo.add_argument("--img-format", default="RGB", choices=("RGB", "BGR"), help="image input channel order")
    demo.add_argument("--metadata-dataset", default="coco_2017_val", help="metadata catalog name")
    demo.add_argument("--confidence-threshold", type=float, default=0.5, help="visualization threshold")
    demo.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra config override appended to the source command",
    )

    analyze = subparsers.add_parser(
        "analyze",
        parents=[format_parent],
        help="build a model-analysis command",
    )
    analyze.add_argument(
        "--tasks",
        nargs="+",
        required=True,
        choices=("flop", "activation", "parameter", "structure"),
        help="analysis tasks to request",
    )
    analyze.add_argument("--config-file", required=True, metavar="FILE", help="lazy config file")
    analyze.add_argument(
        "--num-inputs",
        type=int,
        default=100,
        help="number of sampled inputs for data-dependent metrics",
    )
    analyze.add_argument("--checkpoint", metavar="FILE", help="checkpoint to map to train.init_checkpoint")
    analyze.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra config override appended to the source command",
    )

    vis_data = subparsers.add_parser(
        "visualize-data",
        parents=[format_parent],
        help="build a dataset or dataloader visualization command",
    )
    vis_data.add_argument("--source", required=True, choices=("annotation", "dataloader"), help="visualization source")
    vis_data.add_argument("--config-file", required=True, metavar="FILE", help="lazy config file")
    vis_data.add_argument("--output-dir", required=True, metavar="DIR", help="directory for rendered images")
    vis_data.add_argument("--show", action="store_true", help="open a window instead of saving files")
    vis_data.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra config override appended to the source command",
    )

    vis_json = subparsers.add_parser(
        "visualize-json",
        parents=[format_parent],
        help="build a prediction-visualization command",
    )
    vis_json.add_argument("--input", required=True, metavar="FILE", help="prediction JSON file")
    vis_json.add_argument("--output", required=True, metavar="DIR", help="directory for rendered results")
    vis_json.add_argument("--dataset", default="coco_2017_val", help="registered dataset name")
    vis_json.add_argument("--conf-threshold", type=float, default=0.5, help="visualization threshold")

    benchmark = subparsers.add_parser(
        "benchmark",
        parents=[format_parent],
        help="build a benchmark command",
    )
    benchmark.add_argument("--task", required=True, choices=("train", "eval", "data", "data_advanced"), help="benchmark task")
    benchmark.add_argument("--config-file", required=True, metavar="FILE", help="lazy config file")
    benchmark.add_argument("--checkpoint", metavar="FILE", help="checkpoint to map to train.init_checkpoint")
    benchmark.add_argument("--num-gpus", type=int, default=1, help="GPU count passed to the launcher")
    benchmark.add_argument("--num-machines", type=int, default=1, help="machine count passed to the launcher")
    benchmark.add_argument("--machine-rank", type=int, default=0, help="rank of this machine")
    benchmark.add_argument("--dist-url", default="auto", help="distributed URL or auto")
    benchmark.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra config override appended to the source command",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.workflow == "demo":
        plan = build_demo_plan(args, parser)
    elif args.workflow == "analyze":
        plan = build_analyze_plan(args)
    elif args.workflow == "visualize-data":
        plan = build_visualize_data_plan(args)
    elif args.workflow == "visualize-json":
        plan = build_visualize_json_plan(args)
    elif args.workflow == "benchmark":
        plan = build_benchmark_plan(args, parser)
    else:  # pragma: no cover - defensive fallback
        parser.error(f"Unknown workflow: {args.workflow}")
        return

    if args.format == "json":
        print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))
    else:
        for warning in plan.warnings:
            print(f"note: {warning}", file=sys.stderr)
        print(plan.command)


if __name__ == "__main__":
    main()

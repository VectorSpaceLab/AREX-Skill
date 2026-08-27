#!/usr/bin/env python3
"""Build safe InternImage autonomous-driving command templates.

The helper is dry-run only: it imports no InternImage, OpenMMLab, or
OpenLane-V2 modules and never launches training, evaluation, downloads,
preprocessing, or CUDA builds. It prints shell commands for a prepared checkout.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_REPO_PLACEHOLDER = "<INTERNIMAGE_REPO>"
DEFAULT_CHECKPOINT_PLACEHOLDER = "<CHECKPOINT.pth>"


@dataclass(frozen=True)
class Baseline:
    key: str
    title: str
    workdir: str
    variants: Dict[str, str]
    default_variant: str
    pythonpath_parts: Tuple[str, ...]
    stack_note: str
    test_default_metric: str
    test_requires_distributed: bool = False


BASELINES: Dict[str, Baseline] = {
    "occupancy": Baseline(
        key="occupancy",
        title="CVPR23 Occupancy Prediction / BEVFormerOcc baseline",
        workdir="autonomous_driving/occupancy_prediction",
        variants={
            "intern-s": "projects/configs/bevformer/bevformer_intern-s_occ.py",
            "base": "projects/configs/bevformer/bevformer_base_occ.py",
            "small": "projects/configs/bevformer/bevformer_small_occ.py",
        },
        default_variant="intern-s",
        pythonpath_parts=(".", "projects"),
        stack_note=(
            "Real occupancy runs need the mmdet3d 0.18.x-era stack, nuScenes/Occ3D "
            "data, CUDA GPUs, compatible PyTorch/mmcv, and the InternImage DCNv3 op."
        ),
        test_default_metric="bbox",
        test_requires_distributed=True,
    ),
    "hd-map": Baseline(
        key="hd-map",
        title="Online HD Map Construction / VectorMapNet baseline",
        workdir="autonomous_driving/Online-HD-Map-Construction",
        variants={
            "intern": "src/configs/vectormapnet_intern.py",
            "base": "src/configs/vectormapnet.py",
        },
        default_variant="intern",
        pythonpath_parts=(".", "src"),
        stack_note=(
            "Real HD-map runs need a mmdet3d 1.0.0rc6-era stack, Argoverse 2 "
            "challenge data, CUDA GPUs, compatible PyTorch/mmcv, and DCNv3 for InternImage."
        ),
        test_default_metric="",
    ),
    "openlane": Baseline(
        key="openlane",
        title="CVPR23 OpenLane-V2 scene-structure/topology baseline",
        workdir="autonomous_driving/openlane-v2",
        variants={
            "intern-s": "plugin/mmdet3d/configs/internimage-s.py",
            "baseline": "plugin/mmdet3d/configs/baseline.py",
            "baseline-large": "plugin/mmdet3d/configs/baseline_large.py",
        },
        default_variant="intern-s",
        pythonpath_parts=(".", "plugin"),
        stack_note=(
            "Real OpenLane-V2 runs need the devkit, preprocessed subset_A collections, "
            "a mmdet3d 1.0.0rc6-era stack, CUDA GPUs, and DCNv3 for the InternImage backbone."
        ),
        test_default_metric="openlane",
    ),
}


class CommandError(Exception):
    """Raised for command-construction errors that should become parser errors."""


def shell_join(parts: Iterable[object]) -> str:
    """Return a shell-quoted command line."""
    return " ".join(shlex.quote(str(part)) for part in parts)


def setup_lines(repo_root: Optional[str], baseline: Baseline) -> List[str]:
    if repo_root:
        root_line = "export REPO_ROOT=" + shlex.quote(repo_root)
    else:
        root_line = f'export REPO_ROOT="${{REPO_ROOT:-{DEFAULT_REPO_PLACEHOLDER}}}"'
    pp = ":".join("$PWD" if part == "." else f"$PWD/{part}" for part in baseline.pythonpath_parts)
    return [
        root_line,
        f'cd "$REPO_ROOT/{baseline.workdir}"',
        f'export PYTHONPATH="{pp}:${{PYTHONPATH:-}}"',
    ]


def linewrap(argv: List[str], width: int = 110) -> List[str]:
    quoted = [shlex.quote(str(part)) for part in argv]
    if len(" ".join(quoted)) <= width:
        return [" ".join(quoted)]
    lines = [quoted[0] + " \\"]
    for idx, token in enumerate(quoted[1:], 1):
        suffix = " \\" if idx < len(quoted) - 1 else ""
        lines.append(f"  {token}{suffix}")
    return lines


def add_if(argv: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None and value != "":
        argv.extend([flag, str(value)])


def add_bool(argv: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        argv.append(flag)


def add_many(argv: List[str], flag: str, values: List[str]) -> None:
    if values:
        argv.append(flag)
        argv.extend(values)


def key_value(text: str) -> str:
    if "=" not in text:
        raise argparse.ArgumentTypeError("expected KEY=VALUE, for example data_root=CHANGE_ME")
    key, _value = text.split("=", 1)
    if not key.strip():
        raise argparse.ArgumentTypeError("KEY in KEY=VALUE must not be empty")
    return text


def combined_values(single: Optional[List[str]], many: Optional[List[str]]) -> List[str]:
    values: List[str] = []
    if single:
        values.extend(single)
    if many:
        values.extend(many)
    return values


def selected_config(args: argparse.Namespace, baseline: Baseline) -> Tuple[str, str, List[str]]:
    notes: List[str] = []
    if args.config and args.variant:
        raise CommandError("use only one of --config or --variant")
    if args.config:
        notes.append("Using explicit --config; no built-in variant validation was applied.")
        return args.config, "custom", notes
    variant = args.variant or baseline.default_variant
    if variant not in baseline.variants:
        choices = ", ".join(sorted(baseline.variants))
        raise CommandError(f"unknown --variant {variant!r} for {baseline.key}; choices: {choices}")
    return baseline.variants[variant], variant, notes


def uses_distributed(args: argparse.Namespace, baseline: Baseline, base_mode: str) -> bool:
    if args.gpus < 1:
        raise CommandError("--gpus must be >= 1")
    if args.nnodes < 1:
        raise CommandError("--nnodes must be >= 1")
    forced_by_mode = args.mode.startswith("dist-")
    if args.launcher == "none":
        if forced_by_mode:
            raise CommandError("dist-* modes cannot be combined with --launcher none")
        if baseline.test_requires_distributed and base_mode == "test":
            raise CommandError("occupancy tools/test.py disables non-distributed execution; use --launcher pytorch")
        return False
    if args.launcher == "pytorch" or forced_by_mode:
        return True
    return args.gpus > 1 or (baseline.test_requires_distributed and base_mode == "test")


def launcher_prefix(args: argparse.Namespace, distributed: bool) -> List[str]:
    if not distributed:
        return [args.python]
    port = args.port
    return [
        args.python,
        "-m",
        "torch.distributed.launch",
        f"--nnodes={args.nnodes}",
        f"--node_rank={args.node_rank}",
        f"--master_addr={args.master_addr}",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={port}",
    ]


def normalize_operation(args: argparse.Namespace) -> str:
    if args.format_only:
        if args.operation and args.operation != "format":
            raise CommandError("--format-only conflicts with --operation eval")
        return "format"
    return args.operation or "eval"


def train_argv(args: argparse.Namespace, baseline: Baseline, config: str, distributed: bool, notes: List[str]) -> List[str]:
    argv = launcher_prefix(args, distributed)
    argv.extend(["tools/train.py", config])
    if distributed:
        argv.extend(["--launcher", "pytorch"])
    else:
        if baseline.key in {"occupancy", "hd-map"}:
            argv.extend(["--gpus", str(args.gpus)])
        elif baseline.key == "openlane":
            argv.extend(["--gpu-id", str(args.gpu_id)])

    add_if(argv, "--work-dir", args.work_dir)
    add_if(argv, "--resume-from", args.resume_from)
    add_bool(argv, "--no-validate", args.no_validate)
    add_if(argv, "--seed", args.seed)
    add_bool(argv, "--deterministic", args.deterministic or baseline.key == "occupancy")
    add_bool(argv, "--autoscale-lr", args.autoscale_lr)

    if args.auto_resume:
        if baseline.key == "openlane":
            argv.append("--auto-resume")
        else:
            notes.append("Omitted --auto-resume: only the OpenLane-V2 train parser exposes that flag in this checkout.")
    if args.diff_seed:
        if baseline.key == "openlane":
            argv.append("--diff-seed")
        else:
            notes.append("Omitted --diff-seed: only the OpenLane-V2 train parser exposes that flag in this checkout.")

    add_many(argv, "--cfg-options", combined_values(args.cfg_option, args.cfg_options))
    argv.extend(args.extra_arg or [])
    return argv


def append_common_test_flags(
    argv: List[str],
    args: argparse.Namespace,
    baseline: Baseline,
    operation: str,
    notes: List[str],
) -> None:
    if baseline.key == "openlane" and operation != "eval" and (
        args.dump_dir or args.visualization_dir or args.visualization_num is not None
    ):
        raise CommandError("--dump-dir and --visualization-* require --operation eval for OpenLane-V2")
    add_bool(argv, "--fuse-conv-bn", args.fuse_conv_bn)
    add_bool(argv, "--gpu-collect", args.gpu_collect)
    add_if(argv, "--tmpdir", args.tmpdir)
    add_if(argv, "--seed", args.seed)
    add_bool(argv, "--deterministic", args.deterministic)

    if baseline.key in {"occupancy", "openlane"}:
        if args.out:
            if baseline.key == "occupancy":
                notes.append("Omitted --out for occupancy: inspected tools/test.py accepts the flag but asserts before dumping outputs.")
            else:
                argv.extend(["--out", args.out])
        add_bool(argv, "--show", args.show)
        add_if(argv, "--show-dir", args.show_dir)
        add_many(argv, "--cfg-options", combined_values(args.cfg_option, args.cfg_options))
    elif combined_values(args.cfg_option, args.cfg_options):
        notes.append("Omitted --cfg-option(s): the HD-map test parser does not expose --cfg-options; use a local config copy for test-time data changes.")

    if args.show_dir and baseline.key == "hd-map":
        notes.append("Omitted --show-dir: the HD-map test parser does not expose visualization output flags.")
    if args.show and baseline.key == "hd-map":
        notes.append("Omitted --show: the HD-map test parser does not expose interactive show flags.")

    eval_options = combined_values(args.eval_option, args.eval_options)
    if baseline.key == "openlane":
        if args.dump_dir:
            eval_options.extend(["dump=True", f"dump_dir={args.dump_dir}"])
            notes.append("OpenLane-V2 dump=True writes result.pkl only after the source check_results path and submission metadata are fixed/valid.")
        if args.visualization_num is not None and not args.visualization_dir:
            raise CommandError("--visualization-num requires --visualization-dir")
        if args.visualization_dir:
            eval_options.extend(["visualization=True", f"visualization_dir={args.visualization_dir}"])
            if args.visualization_num is not None:
                eval_options.append(f"visualization_num={args.visualization_num}")
    elif args.dump_dir or args.visualization_dir or args.visualization_num is not None:
        raise CommandError("--dump-dir/--visualization-* apply only to --baseline openlane")

    if baseline.key in {"occupancy", "openlane"}:
        add_many(argv, "--eval-options", eval_options)
    elif eval_options:
        notes.append("Omitted --eval-option(s): the HD-map test parser does not expose --eval-options.")

    if args.eval_fscore:
        if baseline.key == "occupancy" and operation == "eval":
            argv.append("--eval_fscore")
        else:
            notes.append("Omitted --eval-fscore: it is specific to occupancy evaluation mode.")


def test_argv(args: argparse.Namespace, baseline: Baseline, config: str, distributed: bool, notes: List[str]) -> List[str]:
    operation = normalize_operation(args)
    if operation not in {"eval", "format"}:
        raise CommandError(f"unsupported --operation {operation!r}")
    if baseline.key == "openlane" and operation == "format":
        raise CommandError("OpenLane-V2 format-only mode is not a stable submission path in this checkout; use --operation eval with --dump-dir")

    checkpoint = args.checkpoint or DEFAULT_CHECKPOINT_PLACEHOLDER
    argv = launcher_prefix(args, distributed)
    argv.extend(["tools/test.py", config, checkpoint])
    if distributed:
        argv.extend(["--launcher", "pytorch"])
    elif baseline.key == "openlane":
        argv.extend(["--gpu-id", str(args.gpu_id)])

    if baseline.key == "hd-map":
        split = args.split or "val"
        if split not in {"val", "test"}:
            raise CommandError("--split for hd-map must be val or test")
        if split == "test" and operation == "eval":
            raise CommandError("HD-map source test.py refuses evaluation on the hidden test split; use --operation format")
        argv.extend(["--split", split])
    elif args.split:
        notes.append("Omitted --split: only the HD-map test parser exposes it. For OpenLane-V2, point data.test.collection via config/cfg-options.")

    if operation == "format":
        argv.append("--format-only")
        if baseline.key == "openlane":
            notes.append("OpenLane-V2 source test.py exposes --format-only, but submission dumping is normally done through --operation eval --dump-dir.")
    else:
        if baseline.key == "hd-map":
            argv.append("--eval")
        else:
            metric = args.eval_metric or [baseline.test_default_metric]
            add_many(argv, "--eval", metric)

    add_if(argv, "--work-dir", args.work_dir)
    append_common_test_flags(argv, args, baseline, operation, notes)
    argv.extend(args.extra_arg or [])
    return argv


def build_command(args: argparse.Namespace) -> Dict[str, Any]:
    if args.baseline not in BASELINES:
        raise CommandError("--baseline is required unless --list is used")
    if args.mode is None:
        raise CommandError("--mode is required unless --list is used")

    baseline = BASELINES[args.baseline]
    config, variant, config_notes = selected_config(args, baseline)
    notes: List[str] = []
    notes.extend(config_notes)
    notes.append(baseline.stack_note)
    if args.dry_run:
        notes.append("--dry-run was supplied; this helper is always dry-run and only prints templates.")

    base_mode = args.mode.replace("dist-", "")
    if base_mode not in {"train", "test"}:
        raise CommandError("--mode must be train, test, dist-train, or dist-test")

    distributed = uses_distributed(args, baseline, base_mode)
    if base_mode == "train":
        argv = train_argv(args, baseline, config, distributed, notes)
    else:
        argv = test_argv(args, baseline, config, distributed, notes)

    lines = setup_lines(args.repo_root, baseline)
    lines.extend(linewrap(argv))
    notes.append("Printed command is a template only; confirm datasets, checkpoints, write directories, CUDA/DCNv3, and challenge data-use terms before execution.")
    if baseline.key == "openlane":
        notes.append("Known source issue: openlanev2.evaluation.evaluate fails until check_results is exported from preprocessing/__init__.py or evaluate.py imports it from preprocessing.check.")
    return {
        "baseline": baseline.key,
        "title": baseline.title,
        "mode": args.mode,
        "variant": variant,
        "config": config,
        "distributed": distributed,
        "command": "\n".join(lines),
        "notes": notes,
    }


def print_baselines() -> None:
    for key in sorted(BASELINES):
        baseline = BASELINES[key]
        print(f"{key}: {baseline.title}")
        print(f"  workdir: {baseline.workdir}")
        print(f"  default_variant: {baseline.default_variant}")
        for variant, config in sorted(baseline.variants.items()):
            marker = " (default)" if variant == baseline.default_variant else ""
            print(f"  variant {variant}{marker}: {config}")
        print(f"  note: {baseline.stack_note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print dry-run InternImage autonomous-driving command templates.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--list", "--list-baselines", dest="list_baselines", action="store_true", help="List baseline variants/defaults and exit.")
    parser.add_argument("--baseline", choices=sorted(BASELINES), help="Autonomous-driving baseline family.")
    parser.add_argument("--mode", choices=["train", "test", "dist-train", "dist-test"], help="Template mode. train/test choose distributed automatically when --gpus > 1; dist-* force torch.distributed.launch.")
    parser.add_argument("--variant", help="Built-in config variant for the selected baseline. Run --list to see valid values.")
    parser.add_argument("--config", help="Explicit config path relative to the baseline workdir; mutually exclusive with --variant.")
    parser.add_argument("--repo-root", help="Path to a user's InternImage checkout. If omitted, emitted commands use REPO_ROOT or <INTERNIMAGE_REPO>.")
    parser.add_argument("--python", default="python", help="Python executable to place in the emitted command.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format for the generated plan.")
    parser.add_argument("--dry-run", action="store_true", help="Accepted as an explicit no-op guard; this helper is always dry-run only.")

    parser.add_argument("--gpus", type=int, default=8, help="Processes/GPUs per node for distributed templates; use 1 for single-process-capable flows.")
    parser.add_argument("--launcher", choices=["auto", "pytorch", "none"], default="auto", help="Distributed launcher selection for source entrypoints.")
    parser.add_argument("--port", default="29500", help="Distributed master port.")
    parser.add_argument("--nnodes", type=int, default=1, help="Number of nodes for torch.distributed.launch.")
    parser.add_argument("--node-rank", dest="node_rank", type=int, default=0, help="Node rank for multi-node distributed launch.")
    parser.add_argument("--master-addr", default="127.0.0.1", help="Master address for distributed launch.")
    parser.add_argument("--gpu-id", type=int, default=0, help="Single-process GPU id for OpenLane-V2 non-distributed train/test templates.")

    parser.add_argument("--work-dir", help="Working/output directory passed to supported train/test parsers.")
    parser.add_argument("--resume-from", help="Checkpoint to resume training from when supported.")
    parser.add_argument("--auto-resume", action="store_true", help="Append --auto-resume when supported by the source train parser.")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation during training when supported.")
    parser.add_argument("--seed", default="0", help="Seed value passed to source train/test parsers.")
    parser.add_argument("--deterministic", action="store_true", help="Request deterministic CUDNN behavior; occupancy train also preserves the source deterministic default.")
    parser.add_argument("--autoscale-lr", action="store_true", help="Append --autoscale-lr for train parsers.")
    parser.add_argument("--diff-seed", action="store_true", help="Append --diff-seed for OpenLane-V2 training.")
    parser.add_argument("--cfg-option", action="append", type=key_value, default=[], metavar="KEY=VALUE", help="Repeatable OpenMMLab config override; emitted under --cfg-options when supported.")
    parser.add_argument("--cfg-options", nargs="+", type=key_value, metavar="KEY=VALUE", help="One or more OpenMMLab config overrides.")
    parser.add_argument("--extra-arg", action="append", default=[], help="Append one raw source CLI token. Repeat; use --extra-arg=--flag for leading dashes.")

    parser.add_argument("--checkpoint", help="Checkpoint for test modes; defaults to a visible placeholder.")
    parser.add_argument("--operation", choices=["eval", "format"], default="eval", help="High-level test operation mapped to source --eval or --format-only.")
    parser.add_argument("--format-only", action="store_true", help="Legacy alias for --operation format.")
    parser.add_argument("--split", choices=["val", "test"], help="HD-map split. OpenLane-V2 uses config data.test instead of a --split CLI flag.")
    parser.add_argument("--eval-metric", "--eval", dest="eval_metric", nargs="+", help="Metric token(s) for occupancy/OpenLane-V2 source --eval; defaults are baseline-specific.")
    parser.add_argument("--eval-fscore", action="store_true", help="Append occupancy-specific --eval_fscore during evaluation.")
    parser.add_argument("--out", help="Raw output pickle path when the selected source test parser supports it.")
    parser.add_argument("--fuse-conv-bn", action="store_true", help="Append source --fuse-conv-bn for test modes.")
    parser.add_argument("--show", action="store_true", help="Append source --show when supported.")
    parser.add_argument("--show-dir", help="Directory where supported source test parsers save shown results.")
    parser.add_argument("--gpu-collect", action="store_true", help="Use GPU collection for distributed test results when supported.")
    parser.add_argument("--tmpdir", help="Temporary directory for CPU collection in distributed test modes.")
    parser.add_argument("--eval-option", action="append", type=key_value, default=[], metavar="KEY=VALUE", help="Repeatable evaluator option emitted under --eval-options when supported.")
    parser.add_argument("--eval-options", nargs="+", type=key_value, metavar="KEY=VALUE", help="One or more evaluator options emitted under --eval-options when supported.")
    parser.add_argument("--dump-dir", help="OpenLane-V2 convenience option: adds eval-options dump=True dump_dir=<DIR>.")
    parser.add_argument("--visualization-dir", help="OpenLane-V2 convenience option: adds eval-options visualization=True visualization_dir=<DIR>.")
    parser.add_argument("--visualization-num", type=int, help="OpenLane-V2 visualization_num evaluator option; requires --visualization-dir.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_baselines:
        print_baselines()
        return 0
    try:
        plan = build_command(args)
    except CommandError as exc:
        parser.error(str(exc))
        return 2

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print("# Dry-run command template; review placeholders and prerequisites before execution.")
        for note in plan["notes"]:
            print(f"# - {note}")
        print(plan["command"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

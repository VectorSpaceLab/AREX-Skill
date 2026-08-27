#!/usr/bin/env python3
"""Validate a DINO training plan and print a command without launching it.

This utility intentionally has no repository imports and never starts a child
process.  It statically reads Python config assignments (including _base_
files) so that command planning is safe even when a config contains arbitrary
Python code.
"""
from __future__ import annotations

import argparse
import ast
import json
import shlex
import sys
from pathlib import Path
from typing import Any


PARSER_KEYS = {
    "config_file", "options", "dataset_file", "coco_path", "coco_panoptic_path",
    "remove_difficult", "fix_size", "output_dir", "note", "device", "seed",
    "resume", "pretrain_model_path", "finetune_ignore", "start_epoch", "eval",
    "num_workers", "test", "debug", "find_unused_params", "save_results",
    "save_log", "world_size", "dist_url", "rank", "local_rank", "amp",
}
KNOWN_BACKBONES = {
    "resnet50", "resnet101", "swin_T_224_1k", "swin_B_224_22k",
    "swin_B_384_22k", "swin_L_224_22k", "swin_L_384_22k",
    "convnext_xlarge_22k",
}
# These are intentionally accepted even when a base config does not declare
# them: the model's backbone builder consumes backbone_dir as an optional
# runtime-provided attribute.
RUNTIME_CONFIG_KEYS = {"backbone_dir"}
SWIN_BACKBONES = {name for name in KNOWN_BACKBONES if name.startswith("swin_")}


class PlanError(ValueError):
    """An actionable invalid plan or config error."""


def _literal(node: ast.AST, label: str) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as exc:
        raise PlanError(f"{label} must be a literal value for static validation") from exc


def _config_assignments(path: Path, seen: set[Path] | None = None) -> dict[str, Any]:
    """Load literal assignments from a config and its relative _base_ files."""
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        raise PlanError(f"cyclic config _base_ reference involving {path}")
    if not path.is_file():
        raise PlanError(f"config file does not exist: {path}")
    if path.suffix != ".py":
        raise PlanError(f"DINO configs must be Python files: {path}")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise PlanError(f"config has invalid Python syntax: {path}: {exc}") from exc

    seen.add(path)
    local: dict[str, Any] = {}
    base_node: ast.AST | None = None
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "_base_":
                    base_node = node.value
                    break

    if base_node is not None:
        bases = _literal(base_node, f"_base_ in {path}")
        if isinstance(bases, str):
            bases = [bases]
        if not isinstance(bases, list) or not all(isinstance(item, str) for item in bases):
            raise PlanError(f"_base_ in {path} must be a string or list of strings")
        for base in bases:
            local.update(_config_assignments(path.parent / base, seen))

    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id != "_base_":
                try:
                    local[target.id] = _literal(node.value, f"{target.id} in {path}")
                except PlanError:
                    # Non-literal imports or helper expressions are not needed
                    # for the command plan; required fields are checked below.
                    pass
    seen.remove(path)
    return local


def _parse_option(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise PlanError(f"invalid option {raw!r}; use KEY=VALUE")
    key, raw_value = raw.split("=", 1)
    if not key or not key.replace("_", "").replace(".", "").isalnum():
        raise PlanError(f"invalid config option key {key!r}")
    value_text = raw_value
    try:
        value: Any = int(value_text)
    except ValueError:
        try:
            value = float(value_text)
        except ValueError:
            lowered = value_text.lower()
            if lowered in {"true", "false"}:
                value = lowered == "true"
            elif lowered in {"none", "null"}:
                value = None
            elif "," in value_text:
                value = [_parse_scalar(item) for item in value_text.split(",")]
            else:
                value = value_text
    return key, value


def _parse_scalar(value_text: str) -> Any:
    try:
        return int(value_text)
    except ValueError:
        try:
            return float(value_text)
        except ValueError:
            lowered = value_text.lower()
            if lowered in {"true", "false"}:
                return lowered == "true"
            if lowered in {"none", "null"}:
                return None
            return value_text


def _value_for_shell(value: Any) -> str:
    if value is True:
        return "True"
    if value is False:
        return "False"
    if value is None:
        return "None"
    if isinstance(value, list):
        return ",".join(_value_for_shell(item) for item in value)
    return str(value)


def _quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _resolve_repo_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()

def _add_option(options: dict[str, Any], key: str, value: Any, source: str) -> None:
    if key in options:
        raise PlanError(f"config option {key!r} was supplied more than once ({source})")
    if key in PARSER_KEYS:
        raise PlanError(
            f"{key!r} is a main.py command-line argument, not a config option; "
            f"use its explicit command-line flag"
        )
    options[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and print a DINO training command; never launches training."
    )
    parser.add_argument("--repo-root", default=".", help="DINO checkout containing main.py")
    parser.add_argument("--config", required=True, help="config path, relative to --repo-root")
    parser.add_argument("--coco-path", required=True, help="COCO-style dataset root")
    parser.add_argument("--output-dir", required=True, help="non-empty training output directory")
    parser.add_argument("--mode", choices=("single", "torchrun", "submitit"), default="single")
    parser.add_argument("--gpus", type=int, default=1, help="processes/GPUs per node")
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--node-rank", type=int, default=0)
    parser.add_argument("--master-addr", help="required for multi-node torchrun")
    parser.add_argument("--master-port", type=int, default=29500)
    parser.add_argument("--python", default="python", help="Python executable used in the printed command")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--num-workers", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--amp", action="store_true", help="enable mixed precision")
    parser.add_argument("--backbone-dir", help="local pretrained Swin/ConvNeXt directory")
    parser.add_argument("--resume", help="local checkpoint or HTTPS URL for full-state resume")
    parser.add_argument("--pretrain-model-path", help="local model checkpoint for partial fine-tuning")
    parser.add_argument("--finetune-ignore", nargs="+", help="substrings to omit from a pretrain model")
    parser.add_argument("--num-classes", type=int, help="custom COCO category max-id plus one")
    parser.add_argument("--dn-labelbook-size", type=int)
    parser.add_argument("--custom-dataset", action="store_true", help="apply custom-class safety checks")
    parser.add_argument("--option", action="append", default=[], metavar="KEY=VALUE", help="repeatable config override")
    parser.add_argument("--allow-unknown-option", action="store_true")
    parser.add_argument("--allow-missing-data", action="store_true", help="plan without requiring --coco-path to exist")
    # Submitit-specific arguments mirror run_with_submitit.py.
    parser.add_argument("--job-dir", help="required Submitit folder; %%j is allowed")
    parser.add_argument("--job-name", default="DINO")
    parser.add_argument("--timeout", type=int, default=60, help="Submitit timeout in minutes")
    parser.add_argument("--cpus-per-task", type=int, default=16)
    parser.add_argument("--qos")
    parser.add_argument("--requeue", action="store_true")
    return parser


def validate_and_build(args: argparse.Namespace) -> tuple[str, dict[str, Any], list[str]]:
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "main.py").is_file():
        raise PlanError(f"--repo-root does not look like a DINO checkout: {repo_root}")
    if args.gpus < 1 or args.nodes < 1:
        raise PlanError("--gpus and --nodes must be positive")
    if not args.output_dir.strip():
        raise PlanError("--output-dir must be non-empty; main.py cannot save to an empty path")
    if args.mode == "single" and (args.gpus != 1 or args.nodes != 1):
        raise PlanError("single mode uses one process; choose torchrun or submitit for multiple GPUs")
    if args.mode == "submitit" and not args.job_dir:
        raise PlanError("Submitit mode requires --job-dir")
    if args.mode == "torchrun" and args.nodes > 1 and not args.master_addr:
        raise PlanError("multi-node torchrun requires --master-addr")
    if args.node_rank < 0 or args.node_rank >= args.nodes:
        raise PlanError("--node-rank must be in [0, nodes)")
    if args.master_port < 1 or args.master_port > 65535:
        raise PlanError("--master-port must be between 1 and 65535")
    if args.timeout < 1 or args.cpus_per_task < 1:
        raise PlanError("Submitit timeout and CPUs must be positive")
    if args.resume and args.pretrain_model_path:
        raise PlanError("choose --resume or --pretrain-model-path, not both; main.py gives resume precedence")

    config = _resolve_repo_path(repo_root, args.config)
    values = _config_assignments(config)
    options: dict[str, Any] = {}
    for raw in args.option:
        key, value = _parse_option(raw)
        if key == "backbone_dir":
            value = str(_resolve_repo_path(repo_root, str(value)))
        _add_option(options, key, value, "--option")
    if args.num_classes is not None:
        _add_option(options, "num_classes", args.num_classes, "--num-classes")
    if args.dn_labelbook_size is not None:
        _add_option(options, "dn_labelbook_size", args.dn_labelbook_size, "--dn-labelbook-size")
    if args.backbone_dir is not None:
        _add_option(options, "backbone_dir", str(_resolve_repo_path(repo_root, args.backbone_dir)), "--backbone-dir")

    unknown = sorted(key for key in options if key not in values and key not in RUNTIME_CONFIG_KEYS)
    if unknown and not args.allow_unknown_option:
        raise PlanError("unknown config option(s): " + ", ".join(unknown) + "; check the config or pass --allow-unknown-option deliberately")
    effective = dict(values)
    effective.update(options)
    required = ("modelname", "backbone", "num_feature_levels", "return_interm_indices", "batch_size", "epochs", "lr_drop", "num_classes", "dn_labelbook_size")
    missing = [key for key in required if key not in effective]
    if missing:
        raise PlanError("config is missing required DINO training key(s): " + ", ".join(missing))
    if effective["modelname"] != "dino":
        raise PlanError(f"this route supports modelname=dino, got {effective['modelname']!r}")
    if effective["backbone"] not in KNOWN_BACKBONES:
        raise PlanError(f"unsupported DINO backbone {effective['backbone']!r}; known: {sorted(KNOWN_BACKBONES)}")
    levels = effective["num_feature_levels"]
    indices = effective["return_interm_indices"]
    if levels not in (4, 5):
        raise PlanError("training route expects num_feature_levels to be 4 or 5")
    expected_indices = [1, 2, 3] if levels == 4 else [0, 1, 2, 3]
    if indices != expected_indices:
        raise PlanError(f"{levels}-scale DINO requires return_interm_indices={expected_indices}, got {indices!r}")
    if effective["batch_size"] < 1 or effective["epochs"] < 1 or effective["lr_drop"] < 1:
        raise PlanError("batch_size, epochs, and lr_drop must be positive")
    if effective["num_classes"] < 2:
        raise PlanError("num_classes must be at least 2 because category id 1 requires max_id + 1")
    if effective["dn_labelbook_size"] < 1:
        raise PlanError("dn_labelbook_size must be positive")
    if args.custom_dataset:
        explicit_num_classes = args.num_classes is not None or "num_classes" in options
        if not explicit_num_classes and effective["num_classes"] == 91:
            raise PlanError("custom data requires explicit --num-classes or --option num_classes=... (category max-id plus one)")
        if effective["dn_labelbook_size"] < effective["num_classes"] + 1:
            raise PlanError("for custom data follow the repository README rule dn_labelbook_size >= num_classes + 1")
    elif args.num_classes is not None and effective["dn_labelbook_size"] < args.num_classes + 1:
        raise PlanError("custom --num-classes requires --dn-labelbook-size >= num_classes + 1")

    backbone = effective["backbone"]
    if backbone in SWIN_BACKBONES | {"convnext_xlarge_22k"}:
        if "backbone_dir" not in effective:
            raise PlanError(f"{backbone} requires a local pretrained directory via --backbone-dir or backbone_dir=...")
        backbone_dir = _resolve_repo_path(repo_root, str(effective["backbone_dir"]))
        if not backbone_dir.is_dir():
            raise PlanError(f"pretrained backbone directory does not exist: {backbone_dir}")
        effective["backbone_dir"] = str(backbone_dir)
    elif args.backbone_dir:
        raise PlanError("--backbone-dir is only valid for Swin or ConvNeXt configurations")

    data_path = _resolve_repo_path(repo_root, args.coco_path)
    output_dir = _resolve_repo_path(repo_root, args.output_dir)
    warnings: list[str] = []
    if not data_path.is_dir():
        if args.allow_missing_data:
            warnings.append(f"dataset root is missing (allowed for planning only): {data_path}")
        else:
            raise PlanError(f"dataset root does not exist: {data_path}; use --allow-missing-data only for planning")
    if args.mode == "submitit" and args.cpus_per_task != 16:
        warnings.append("run_with_submitit.py parses --cpus_per_task but currently submits a hard-coded 16")
    if args.mode == "submitit":
        warnings.append("Submitit mode requires a working Slurm service and the site's shared-folder setup")
    if args.mode == "torchrun" and args.nodes > 1:
        warnings.append("run the printed multi-node command once per node with its corresponding --node-rank")
    if "dn_scalar" in options or "dn_label_coef" in options or "dn_bbox_coef" in options:
        warnings.append("legacy launcher override detected; current DINO code does not read this key")

    common = ["main.py", "--output_dir", str(output_dir), "-c", str(config), "--coco_path", str(data_path), "--device", args.device]
    if args.num_workers is not None:
        if args.num_workers < 0:
            raise PlanError("--num-workers cannot be negative")
        common += ["--num_workers", str(args.num_workers)]
    if args.seed is not None:
        common += ["--seed", str(args.seed)]
    if args.amp:
        common.append("--amp")
    if args.resume:
        resume = args.resume
        if not resume.startswith("https"):
            resume_path = _resolve_repo_path(repo_root, resume)
            if not resume_path.is_file():
                raise PlanError(f"resume checkpoint does not exist: {resume_path}")
            resume = str(resume_path)
        common += ["--resume", resume]
    if args.pretrain_model_path:
        pretrain = _resolve_repo_path(repo_root, args.pretrain_model_path)
        if not pretrain.is_file():
            raise PlanError(f"pretrain checkpoint does not exist: {pretrain}")
        common += ["--pretrain_model_path", str(pretrain)]
        if args.finetune_ignore:
            common += ["--finetune_ignore", *args.finetune_ignore]
    elif args.finetune_ignore:
        raise PlanError("--finetune-ignore is meaningful only with --pretrain-model-path")

    if args.mode == "single":
        command = [args.python, *common]
    elif args.mode == "torchrun":
        command = [args.python, "-m", "torch.distributed.run", "--nproc_per_node", str(args.gpus)]
        if args.nodes > 1:
            command += ["--nnodes", str(args.nodes), "--node_rank", str(args.node_rank), "--master_addr", str(args.master_addr), "--master_port", str(args.master_port)]
        command += common
    else:
        job_dir = _resolve_repo_path(repo_root, args.job_dir)
        command = [args.python, "run_with_submitit.py", "--timeout", str(args.timeout), "--job_name", args.job_name, "--job_dir", str(job_dir), "--ngpus", str(args.gpus), "--nodes", str(args.nodes), "--cpus_per_task", str(args.cpus_per_task)]
        if args.qos:
            command += ["--qos", args.qos]
        if args.requeue:
            command.append("--requeue")
        command += common[1:]
    if options:
        command += ["--options", *[f"{key}={_value_for_shell(value)}" for key, value in options.items()]]

    world_size = args.gpus * args.nodes if args.mode != "single" else 1
    summary = {"config": str(config), "backbone": backbone, "scales": levels, "per_process_batch_size": effective["batch_size"], "planned_world_size": world_size, "planned_global_batch_size": effective["batch_size"] * world_size, "command_is_print_only": True, "warnings": warnings}
    command_text = "cd " + shlex.quote(str(repo_root)) + " && " + _quote_command(command)
    return command_text, summary, warnings


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        command, summary, warnings = validate_and_build(args)
    except PlanError as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2))
    print("\nCOMMAND (not launched):")
    print(command)
    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

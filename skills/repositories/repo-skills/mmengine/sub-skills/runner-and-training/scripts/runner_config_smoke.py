#!/usr/bin/env python3
"""Validate common MMEngine Runner config-shape mistakes without training.

This helper intentionally avoids importing user project code, building datasets,
constructing Runner, launching distributed jobs, or writing files. It accepts a
JSON file that contains the Runner/FlexibleRunner-relevant portion of a config.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_LAUNCHERS = {"none", "pytorch", "slurm", "mpi"}
VALID_AMP_DTYPES = {None, "float16", "bfloat16"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-check MMEngine Runner/FlexibleRunner config shape.")
    parser.add_argument(
        "--config-json",
        type=Path,
        help="Path to a JSON file containing Runner-relevant config fields.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Validate a tiny built-in train+val example instead of a file.")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero when warnings are found.")
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> dict[str, Any]:
    if args.demo:
        return {
            "model": {"type": "ToyModel"},
            "work_dir": "work_dirs/demo",
            "train_dataloader": {"batch_size": 2, "dataset": {"type": "ToyDataset"}},
            "train_cfg": {"by_epoch": True, "max_epochs": 2, "val_interval": 1},
            "optim_wrapper": {"optimizer": {"type": "SGD", "lr": 0.01}},
            "param_scheduler": {"type": "MultiStepLR", "by_epoch": True, "milestones": [1]},
            "val_dataloader": {"batch_size": 2, "dataset": {"type": "ToyDataset"}},
            "val_cfg": {},
            "val_evaluator": {"type": "Accuracy"},
            "default_hooks": {
                "logger": {"type": "LoggerHook", "log_metric_by_epoch": True},
                "checkpoint": {"type": "CheckpointHook", "interval": 1, "save_best": "accuracy", "rule": "greater"},
            },
        }
    if args.config_json is None:
        raise SystemExit("Provide --config-json or --demo.")
    with args.config_json.open("r", encoding="utf-8") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise SystemExit("The JSON root must be an object/dict.")
    return config


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def has_all(config: dict[str, Any], keys: list[str]) -> bool:
    return all(config.get(key) is not None for key in keys)


def validate(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    runner_type = config.get("runner_type", config.get("type", "Runner"))
    train_cfg = as_dict(config.get("train_cfg"))
    val_cfg_present = "val_cfg" in config and config.get("val_cfg") is not None
    test_cfg_present = "test_cfg" in config and config.get("test_cfg") is not None
    has_train = bool(train_cfg)
    has_val = val_cfg_present or config.get("val_dataloader") is not None or config.get("val_evaluator") is not None
    has_test = test_cfg_present or config.get("test_dataloader") is not None or config.get("test_evaluator") is not None

    if config.get("model") is None:
        errors.append("Missing `model`; Runner requires a model object or model config.")
    if not config.get("work_dir"):
        warnings.append("Missing `work_dir`; runtime logs/checkpoints will not have an explicit project output directory.")

    if has_train:
        for key in ["train_dataloader", "optim_wrapper"]:
            if config.get(key) is None:
                errors.append(f"Training config is present but `{key}` is missing.")
        if not ("max_epochs" in train_cfg or "max_iters" in train_cfg or "type" in train_cfg):
            errors.append("`train_cfg` should declare `max_epochs`, `max_iters`, or an explicit loop `type`.")
        if train_cfg.get("by_epoch") is False and "max_iters" not in train_cfg and "type" not in train_cfg:
            errors.append("Iter-based `train_cfg` should set `max_iters` unless an explicit loop `type` owns it.")
        if train_cfg.get("by_epoch") is True and "max_epochs" not in train_cfg and "type" not in train_cfg:
            errors.append("Epoch-based `train_cfg` should set `max_epochs` unless an explicit loop `type` owns it.")
    elif config.get("train_dataloader") is not None or config.get("optim_wrapper") is not None:
        warnings.append("Training components exist without `train_cfg`; confirm this is not an incomplete training workflow.")

    if has_val and not has_all(config, ["val_dataloader", "val_evaluator"]):
        errors.append("Validation is partially configured; provide both `val_dataloader` and `val_evaluator` with `val_cfg`.")
    if has_test and not has_all(config, ["test_dataloader", "test_evaluator"]):
        errors.append("Testing is partially configured; provide both `test_dataloader` and `test_evaluator` with `test_cfg`.")
    if train_cfg.get("val_interval") is not None and not has_val:
        warnings.append("`train_cfg.val_interval` is set but validation dataloader/evaluator fields are incomplete or absent.")

    validate_optim_wrapper(config.get("optim_wrapper"), has_train, errors, warnings)
    validate_hooks(config, train_cfg, has_val, errors, warnings)
    validate_schedulers(config.get("param_scheduler"), train_cfg, errors, warnings)
    validate_resume(config, runner_type, warnings)
    validate_distributed(config, runner_type, errors, warnings)

    return errors, warnings


def validate_optim_wrapper(value: Any, has_train: bool, errors: list[str], warnings: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        warnings.append("`optim_wrapper` is not a dict; this may be valid only if a live OptimWrapper object is supplied in Python.")
        return
    wrapper_type = value.get("type", "OptimWrapper")
    if "optimizer" not in value and has_train:
        errors.append("`optim_wrapper` should contain an `optimizer` config for normal Runner training.")
    if wrapper_type in {"SGD", "Adam", "AdamW", "RMSprop"}:
        errors.append("`optim_wrapper.type` looks like a raw optimizer; nest it under `optim_wrapper.optimizer.type`.")
    if wrapper_type == "AmpOptimWrapper" and value.get("dtype") not in VALID_AMP_DTYPES:
        errors.append("`AmpOptimWrapper.dtype` should be `float16`, `bfloat16`, null, or omitted.")
    accumulative_counts = value.get("accumulative_counts")
    if accumulative_counts is not None:
        if not isinstance(accumulative_counts, int) or accumulative_counts < 1:
            errors.append("`optim_wrapper.accumulative_counts` must be a positive integer.")
        elif accumulative_counts > 1:
            warnings.append("Gradient accumulation changes effective batch size; review scheduler and batch-norm assumptions.")
    clip_grad = value.get("clip_grad")
    if clip_grad is not None and isinstance(clip_grad, dict):
        if "max_norm" not in clip_grad and "clip_value" not in clip_grad:
            warnings.append("`clip_grad` has neither `max_norm` nor `clip_value`; clipping may be a no-op.")


def validate_hooks(
    config: dict[str, Any],
    train_cfg: dict[str, Any],
    has_val: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    default_hooks = as_dict(config.get("default_hooks"))
    logger = as_dict(default_hooks.get("logger"))
    checkpoint = as_dict(default_hooks.get("checkpoint"))
    train_by_epoch = train_cfg.get("by_epoch")

    if train_by_epoch is False:
        if logger.get("log_metric_by_epoch") is True:
            warnings.append("Iter-based training usually needs `LoggerHook.log_metric_by_epoch=False`.")
        if checkpoint.get("by_epoch") is True:
            warnings.append("Iter-based training usually needs `CheckpointHook.by_epoch=False`.")
        log_processor = as_dict(config.get("log_processor"))
        if log_processor.get("by_epoch") is True:
            warnings.append("Iter-based training usually needs `log_processor.by_epoch=False`.")

    save_best = checkpoint.get("save_best")
    if save_best is not None:
        if not has_val:
            errors.append("Checkpoint `save_best` requires a complete validation workflow.")
        if save_best != "auto" and checkpoint.get("rule") is None:
            warnings.append("Checkpoint `save_best` uses an explicit metric; set `rule='greater'` or `rule='less'`.")

    custom_hooks = config.get("custom_hooks")
    if custom_hooks is not None and not isinstance(custom_hooks, list):
        errors.append("`custom_hooks` should be a list of hook configs or hook objects.")


def validate_schedulers(
    value: Any,
    train_cfg: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if value is None:
        return
    schedulers = as_list(value)
    if not schedulers:
        return
    train_by_epoch = train_cfg.get("by_epoch")
    for index, scheduler in enumerate(schedulers):
        if not isinstance(scheduler, dict):
            warnings.append(f"Scheduler #{index} is not a dict; only live scheduler objects should use this shape.")
            continue
        if "type" not in scheduler:
            errors.append(f"Scheduler #{index} is missing `type`.")
        scheduler_by_epoch = scheduler.get("by_epoch", True)
        if train_by_epoch is False and scheduler_by_epoch is True and not scheduler.get("convert_to_iter_based"):
            warnings.append(
                f"Scheduler #{index} is epoch-based inside iter-based training; convert counts or set `convert_to_iter_based=True`.")
        begin = scheduler.get("begin")
        end = scheduler.get("end")
        if begin is not None and end is not None and begin >= end:
            errors.append(f"Scheduler #{index} has `begin >= end`; expected a valid [begin, end) interval.")


def validate_resume(config: dict[str, Any], runner_type: Any, warnings: list[str]) -> None:
    resume = config.get("resume", False)
    load_from = config.get("load_from")
    if load_from and not resume:
        warnings.append("`load_from` without `resume=True` loads weights only and restarts optimizer/scheduler progress.")
    if isinstance(resume, str) and runner_type != "FlexibleRunner":
        warnings.append("String-valued `resume` is a FlexibleRunner pattern; standard Runner expects a boolean `resume`.")
    if resume is True and not config.get("work_dir") and not load_from:
        warnings.append("Auto resume searches `work_dir`; set `work_dir` or specify `load_from`.")


def validate_distributed(
    config: dict[str, Any],
    runner_type: Any,
    errors: list[str],
    warnings: list[str],
) -> None:
    launcher = config.get("launcher", "none")
    if launcher is not None and launcher not in VALID_LAUNCHERS:
        errors.append(f"Unknown launcher `{launcher}`; expected one of {sorted(VALID_LAUNCHERS)}.")
    env_cfg = as_dict(config.get("env_cfg"))
    dist_cfg = as_dict(env_cfg.get("dist_cfg"))
    backend = dist_cfg.get("backend")
    if launcher == "none" and backend == "nccl":
        warnings.append("`env_cfg.dist_cfg.backend='nccl'` is harmless by default but only meaningful for CUDA distributed runs.")
    if config.get("strategy") is not None and runner_type != "FlexibleRunner":
        errors.append("`strategy` is a FlexibleRunner field; use `FlexibleRunner` for DeepSpeed/FSDP/ColossalAI strategies.")
    strategy = as_dict(config.get("strategy"))
    strategy_type = strategy.get("type")
    if strategy_type in {"DeepSpeedStrategy", "FSDPStrategy", "ColossalAIStrategy"}:
        warnings.append(f"`{strategy_type}` is dependency/hardware gated; verify optional packages, distributed launch, and GPU support.")
    if "compile" in config and runner_type == "Runner":
        warnings.append("Standard Runner compile options usually belong under `cfg=dict(compile=...)`; FlexibleRunner has top-level `compile`.")


def main() -> int:
    args = parse_args()
    config = load_config(args)
    errors, warnings = validate(config)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    if warnings and args.strict_warnings:
        print(f"FAILED: 0 error(s), {len(warnings)} warning(s) under --strict-warnings.")
        return 2
    print(f"OK: 0 error(s), {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

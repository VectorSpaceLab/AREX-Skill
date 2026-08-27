#!/usr/bin/env python3
"""Build a safe dry-run command for pytorch-semseg train.py.

This helper prints a shell command and pre-run warnings. It never imports the
training script, constructs datasets, launches training, downloads files, or
writes logs/checkpoints.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable


def _shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _resolve(path_text: str | None, base: Path) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return base / path


def _load_yaml(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        warnings.append(f"PyYAML is not importable for static inspection: {exc!r}.")
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        warnings.append(f"Could not parse config with yaml.safe_load: {exc}.")
        return None

    if data is None:
        warnings.append("Config is empty; train.py expects model, data, and training sections.")
        return None
    if not isinstance(data, dict):
        warnings.append("Config top level is not a mapping; train.py expects YAML sections.")
        return None
    return data


def _looks_machine_specific(path_text: str) -> bool:
    text = path_text.replace("\\", "/")
    markers = (
        "/private/",
        "/home/",
        "/Users/",
        "/mnt/",
        "/media/",
        "/scratch/",
        "/data/",
        "~",
    )
    return any(marker in text or text.startswith(marker) for marker in markers)


def _check_data_path(label: str, value: Any, base: Path, warnings: list[str]) -> None:
    if value in (None, ""):
        warnings.append(f"{label} is empty; dataset loading will fail unless the loader can infer a path.")
        return
    if not isinstance(value, (str, os.PathLike)):
        warnings.append(f"{label} is not a string path; review the config with data-and-configs.")
        return

    value_text = os.fspath(value)
    resolved = _resolve(value_text, base)
    if Path(value_text).expanduser().is_absolute():
        warnings.append(f"{label} is an absolute path; confirm it is valid on the run machine before training.")
    if _looks_machine_specific(value_text):
        warnings.append(f"{label} looks machine-specific; rewrite the config before sharing or running elsewhere.")
    if resolved is not None and not resolved.exists():
        warnings.append(f"{label} does not exist from the selected run directory; training will fail when the loader reads data.")


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _inspect_config(config_path: Path, run_dir: Path, warnings: list[str]) -> None:
    cfg = _load_yaml(config_path, warnings)
    if cfg is None:
        return

    model = cfg.get("model")
    data = cfg.get("data")
    training = cfg.get("training")

    if not isinstance(model, dict) or not model.get("arch"):
        warnings.append("Config lacks model.arch; route model selection details to model-zoo-and-apis.")

    if not isinstance(data, dict):
        warnings.append("Config lacks a data mapping; route dataset/config repair to data-and-configs.")
    else:
        if not data.get("dataset"):
            warnings.append("Config lacks data.dataset; get_loader(data.dataset) cannot select a loader.")
        if "train_split" not in data:
            warnings.append("Config lacks data.train_split; train.py expects it.")
        if "val_split" not in data:
            warnings.append("Config lacks data.val_split; train.py validates periodically on this split.")
        if "img_rows" not in data or "img_cols" not in data:
            warnings.append("Config lacks data.img_rows or data.img_cols; train.py passes both as img_size.")
        _check_data_path("data.path", data.get("path"), run_dir, warnings)
        if "sbd_path" in data:
            _check_data_path("data.sbd_path", data.get("sbd_path"), run_dir, warnings)

    if not isinstance(training, dict):
        warnings.append("Config lacks a training mapping; train.py expects training settings.")
        return

    required_training_keys = ("train_iters", "batch_size", "val_interval", "n_workers", "print_interval", "optimizer", "loss", "lr_schedule", "resume")
    for key in required_training_keys:
        if key not in training:
            warnings.append(f"Config lacks training.{key}; train.py indexes this key directly or relies on it for loop behavior.")

    if "l_rate" in training or "l_schedule" in training:
        warnings.append("Config has legacy training.l_rate/l_schedule keys; train.py ignores these in favor of training.optimizer and training.lr_schedule.")

    train_iters = _as_int(training.get("train_iters"))
    if train_iters is not None:
        if train_iters > 1000:
            warnings.append(f"training.train_iters={train_iters} is a costly full-run setting; obtain explicit compute approval.")
        elif train_iters <= 0:
            warnings.append("training.train_iters must be positive for a useful run.")

    val_interval = _as_int(training.get("val_interval"))
    if val_interval is not None and val_interval <= 0:
        warnings.append("training.val_interval must be positive; periodic validation modulo logic expects this.")

    batch_size = _as_int(training.get("batch_size"))
    if batch_size is not None and batch_size <= 0:
        warnings.append("training.batch_size must be positive.")

    n_workers = _as_int(training.get("n_workers"))
    cpu_count = os.cpu_count() or 1
    if n_workers is not None:
        if n_workers < 0:
            warnings.append("training.n_workers cannot be negative.")
        elif n_workers > cpu_count:
            warnings.append(f"training.n_workers={n_workers} exceeds detected CPU count {cpu_count}; consider lowering it.")

    optimizer = training.get("optimizer")
    if optimizer is not None and not isinstance(optimizer, dict):
        warnings.append("training.optimizer is not a mapping; get_optimizer expects optimizer.name and parameters.")
    elif isinstance(optimizer, dict) and not optimizer.get("name"):
        warnings.append("training.optimizer lacks name; get_optimizer defaults only when the whole optimizer section is null.")

    if training.get("loss") is None:
        warnings.append("training.loss is null or missing; null selects default cross_entropy, but a missing key raises a config error.")

    resume = training.get("resume")
    if resume not in (None, "", False):
        if not isinstance(resume, (str, os.PathLike)):
            warnings.append("training.resume is not a path string; resume loading will fail.")
        else:
            resume_path = _resolve(os.fspath(resume), run_dir)
            if resume_path is not None and not resume_path.is_file():
                warnings.append("training.resume checkpoint does not exist from the selected run directory; train.py will start from scratch.")



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a dry-run pytorch-semseg train.py command and print warnings without running training."
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Config YAML to pass to train.py. If omitted, the generated command relies on train.py's built-in default.",
    )
    parser.add_argument(
        "--script",
        default="train.py",
        help="Training script path to place in the generated command. Default: train.py",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable or command to place in the generated command. Default: python",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional run directory for relative existence checks and an optional 'cd ... &&' command prefix.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 when missing script/config paths are detected. The command is still printed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    warnings: list[str] = []
    strict_errors: list[str] = []

    run_dir = Path(args.repo_root).expanduser() if args.repo_root else Path.cwd()
    script_path = _resolve(args.script, run_dir)
    if script_path is not None and not script_path.is_file():
        msg = "Training script was not found from the selected run directory; run the printed command from a checkout containing train.py or pass --script."
        warnings.append(msg)
        strict_errors.append(msg)

    command = [args.python, args.script]
    if args.config:
        command.extend(["--config", args.config])
        config_path = _resolve(args.config, run_dir)
        if config_path is None or not config_path.is_file():
            msg = "Config file was not found from the selected run directory; train.py will fail before training."
            warnings.append(msg)
            strict_errors.append(msg)
        else:
            _inspect_config(config_path, run_dir, warnings)
    else:
        warnings.append("No --config supplied; train.py will use its built-in default config path. Prefer an explicit config.")

    warnings.append("train.py uses legacy yaml.load(fp); modern PyYAML may require patching to yaml.safe_load(fp) or using a compatible environment.")
    warnings.append("Full training writes runs/<config-stem>/<random-run-id>/ with TensorBoard events, copied config, logs, and best checkpoints.")
    warnings.append("This helper is a dry run only; it never executes train.py.")

    rendered = _shell_join(command)
    if args.repo_root:
        rendered = f"cd {_shell_join([args.repo_root])} && {rendered}"

    print("DRY-RUN COMMAND:")
    print(rendered)
    print()
    print("WARNINGS:")
    for idx, warning in enumerate(warnings, 1):
        print(f"{idx}. {warning}")

    if args.strict and strict_errors:
        print("\nSTRICT RESULT: missing required script/config path detected.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

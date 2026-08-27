#!/usr/bin/env python3
"""Build a safe dry-run command for pytorch-semseg validate.py.

This helper prints a shell command and pre-run warnings. It never imports the
validation script, loads checkpoints, constructs datasets, launches validation,
downloads files, or writes outputs.
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
        warnings.append("Config is empty; validate.py expects model, data, and training sections.")
        return None
    if not isinstance(data, dict):
        warnings.append("Config top level is not a mapping; validate.py expects YAML sections.")
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
        warnings.append(f"{label} is empty; validation cannot construct the dataset root.")
        return
    if not isinstance(value, (str, os.PathLike)):
        warnings.append(f"{label} is not a string path; review the config with data-and-configs.")
        return

    value_text = os.fspath(value)
    resolved = _resolve(value_text, base)
    if Path(value_text).expanduser().is_absolute():
        warnings.append(f"{label} is an absolute path; confirm it is valid on the run machine before validation.")
    if _looks_machine_specific(value_text):
        warnings.append(f"{label} looks machine-specific; rewrite the config before sharing or running elsewhere.")
    if resolved is not None and not resolved.exists():
        warnings.append(f"{label} does not exist from the selected run directory; validation will fail when the loader reads data.")


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
        warnings.append("Config lacks model.arch; validation cannot construct the checkpoint architecture.")

    if not isinstance(data, dict):
        warnings.append("Config lacks a data mapping; route dataset/config repair to data-and-configs.")
    else:
        if not data.get("dataset"):
            warnings.append("Config lacks data.dataset; get_loader(data.dataset) cannot select a loader.")
        if "val_split" not in data:
            warnings.append("Config lacks data.val_split; validate.py requires it.")
        if "img_rows" not in data or "img_cols" not in data:
            warnings.append("Config lacks data.img_rows or data.img_cols; validate.py passes both as img_size.")
        _check_data_path("data.path", data.get("path"), run_dir, warnings)

    if not isinstance(training, dict):
        warnings.append("Config lacks a training mapping; validate.py uses training.batch_size.")
        return

    if "batch_size" not in training:
        warnings.append("Config lacks training.batch_size; validate.py indexes it directly.")
    batch_size = _as_int(training.get("batch_size"))
    if batch_size is not None and batch_size <= 0:
        warnings.append("training.batch_size must be positive for validation.")

    if "n_workers" in training:
        warnings.append("validate.py ignores training.n_workers and hard-codes DataLoader num_workers=8.")
    else:
        warnings.append("validate.py hard-codes DataLoader num_workers=8; tune the script locally if this is too high.")

    if "l_rate" in training or "l_schedule" in training:
        warnings.append("Config has legacy training.l_rate/l_schedule keys; validation ignores them, but they signal config drift.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a dry-run pytorch-semseg validate.py command and print warnings without running validation."
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Config YAML to pass to validate.py. If omitted, the generated command relies on validate.py's built-in default.",
    )
    parser.add_argument(
        "--model_path",
        "--model-path",
        dest="model_path",
        help="Checkpoint path to pass to validate.py. If omitted, the generated command relies on validate.py's built-in default.",
    )
    parser.add_argument(
        "--script",
        default="validate.py",
        help="Validation script path to place in the generated command. Default: validate.py",
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
    flip = parser.add_mutually_exclusive_group()
    flip.add_argument(
        "--eval_flip",
        dest="eval_flip",
        action="store_true",
        help="Print a command with validate.py flip averaging enabled.",
    )
    flip.add_argument(
        "--no-eval_flip",
        dest="eval_flip",
        action="store_false",
        help="Print a command with validate.py flip averaging disabled.",
    )
    parser.set_defaults(eval_flip=True)

    timing = parser.add_mutually_exclusive_group()
    timing.add_argument(
        "--measure_time",
        dest="measure_time",
        action="store_true",
        help="Print a command with validate.py fps reporting enabled.",
    )
    timing.add_argument(
        "--no-measure_time",
        dest="measure_time",
        action="store_false",
        help="Print a command with validate.py fps reporting disabled.",
    )
    parser.set_defaults(measure_time=True)

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 2 when missing script/config/checkpoint paths are detected. The command is still printed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    warnings: list[str] = []
    strict_errors: list[str] = []

    run_dir = Path(args.repo_root).expanduser() if args.repo_root else Path.cwd()
    script_path = _resolve(args.script, run_dir)
    if script_path is not None and not script_path.is_file():
        msg = "Validation script was not found from the selected run directory; run the printed command from a checkout containing validate.py or pass --script."
        warnings.append(msg)
        strict_errors.append(msg)

    command = [args.python, args.script]
    if args.config:
        command.extend(["--config", args.config])
        config_path = _resolve(args.config, run_dir)
        if config_path is None or not config_path.is_file():
            msg = "Config file was not found from the selected run directory; validate.py will fail before loading the checkpoint."
            warnings.append(msg)
            strict_errors.append(msg)
        else:
            _inspect_config(config_path, run_dir, warnings)
    else:
        warnings.append("No --config supplied; validate.py will use its built-in default config path. Prefer an explicit config.")

    if args.model_path:
        command.extend(["--model_path", args.model_path])
        model_path = _resolve(args.model_path, run_dir)
        if model_path is None or not model_path.is_file():
            msg = "Checkpoint model_path was not found from the selected run directory; validation cannot load model_state."
            warnings.append(msg)
            strict_errors.append(msg)
        elif model_path.is_dir():
            msg = "Checkpoint model_path resolves to a directory, not a checkpoint file."
            warnings.append(msg)
            strict_errors.append(msg)
    else:
        warnings.append("No --model_path supplied; validate.py will use its built-in default checkpoint name. Prefer an explicit checkpoint.")

    command.append("--eval_flip" if args.eval_flip else "--no-eval_flip")
    command.append("--measure_time" if args.measure_time else "--no-measure_time")

    if args.eval_flip:
        warnings.append("--eval_flip roughly doubles validation inference work by averaging original and horizontally flipped outputs.")
    if args.measure_time:
        warnings.append("--measure_time prints approximate per-batch fps; it is not a rigorous benchmark.")

    warnings.append("validate.py uses legacy yaml.load(fp); modern PyYAML may require patching to yaml.safe_load(fp) or using a compatible environment.")
    warnings.append("Validation expects torch.load(model_path)['model_state']; DataParallel 'module.' prefixes are stripped by convert_state_dict.")
    warnings.append("This helper is a dry run only; it never executes validate.py or loads the checkpoint.")

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
        print("\nSTRICT RESULT: missing required script/config/checkpoint path detected.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

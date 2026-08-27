#!/usr/bin/env python3
"""Build and optionally run StyleTTS2 training commands.

Default mode is a dry-run preflight: print the command and perform lightweight
filesystem/config checks. Add --run to execute the long-running training command.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

STAGE_DEFAULT_CONFIG = {
    "first": "Configs/config.yml",
    "second": "Configs/config.yml",
    "finetune": "Configs/config_ft.yml",
    "finetune-accelerate": "Configs/config_ft.yml",
}

STAGE_SCRIPT = {
    "first": "train_first.py",
    "second": "train_second.py",
    "finetune": "train_finetune.py",
    "finetune-accelerate": "train_finetune_accelerate.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely build StyleTTS2 first/second/fine-tune training commands. "
            "Dry-run by default; add --run to execute."
        )
    )
    parser.add_argument(
        "--stage",
        choices=sorted(STAGE_SCRIPT),
        required=True,
        help="Training workflow to build.",
    )
    parser.add_argument(
        "--config",
        help="Config path passed to --config_path. Defaults to Configs/config.yml for first/second and Configs/config_ft.yml for fine-tuning.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the StyleTTS2 source checkout. Defaults to the current directory.",
    )
    parser.add_argument(
        "--num-processes",
        type=int,
        default=None,
        help="Accelerate process count. Defaults to 1 for finetune-accelerate and is optional for first stage.",
    )
    parser.add_argument(
        "--mixed-precision",
        choices=["no", "fp16", "bf16", "fp8"],
        default=None,
        help="Accelerate mixed precision. Defaults to fp16 for finetune-accelerate. Rejected for first stage unless omitted.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the command. Without this flag the helper only prints and checks.",
    )
    parser.add_argument(
        "--allow-no-cuda",
        action="store_true",
        help="Do not fail --run when CUDA is unavailable. This is an expert override; native training is CUDA-oriented.",
    )
    return parser.parse_args()


def rel_or_abs_path(base: Path, value: Optional[str]) -> Optional[Path]:
    if value is None or value == "":
        return None
    p = Path(str(value)).expanduser()
    if not p.is_absolute():
        p = base / p
    return p


def load_yaml(path: Path) -> Tuple[Dict[str, Any], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if importlib.util.find_spec("yaml") is None:
        errors.append("PyYAML is not importable; install pyyaml before training.")
        return {}, warnings, errors
    import yaml  # type: ignore

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - exact parser errors vary
        errors.append(f"Could not parse config {path}: {exc}")
        return {}, warnings, errors
    if not isinstance(data, dict):
        errors.append(f"Config {path} did not parse to a mapping.")
        return {}, warnings, errors
    return data, warnings, errors


def check_path(label: str, path: Optional[Path], required_for_run: bool, warnings: List[str], errors: List[str], expect_dir: Optional[bool] = None) -> None:
    if path is None:
        msg = f"{label} is not configured."
        (errors if required_for_run else warnings).append(msg)
        return
    exists = path.exists()
    type_ok = True
    if exists and expect_dir is True:
        type_ok = path.is_dir()
    elif exists and expect_dir is False:
        type_ok = path.is_file()
    if not exists or not type_ok:
        kind = "directory" if expect_dir else "file" if expect_dir is False else "path"
        msg = f"{label} {kind} not found: {path}"
        (errors if required_for_run else warnings).append(msg)


def config_value(config: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = config
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def resolve_log_dir(repo_root: Path, config: Dict[str, Any]) -> Optional[Path]:
    log_dir = config.get("log_dir")
    return rel_or_abs_path(repo_root, str(log_dir)) if log_dir else None


def resolve_first_stage_checkpoint(repo_root: Path, config: Dict[str, Any]) -> Optional[Path]:
    first_stage = config.get("first_stage_path")
    if not first_stage:
        return None
    first_stage_str = str(first_stage)
    p = Path(first_stage_str).expanduser()
    if p.is_absolute():
        return p
    log_dir = resolve_log_dir(repo_root, config)
    if log_dir is None:
        return None
    return log_dir / p


def check_python_imports(stage: str, warnings: List[str]) -> None:
    needed = ["yaml", "torch", "torchaudio", "transformers", "munch", "librosa", "soundfile", "pandas", "tensorboard"]
    if stage in {"first", "finetune-accelerate"}:
        needed.append("accelerate")
    missing = [name for name in needed if importlib.util.find_spec(name) is None]
    if missing:
        warnings.append("Missing import(s) in the current Python environment: " + ", ".join(sorted(set(missing))))


def check_cuda(warnings: List[str], errors: List[str], require_for_run: bool, allow_no_cuda: bool) -> None:
    if importlib.util.find_spec("torch") is None:
        msg = "Cannot check CUDA because torch is not importable."
        (errors if require_for_run and not allow_no_cuda else warnings).append(msg)
        return
    try:
        import torch  # type: ignore

        available = bool(torch.cuda.is_available())
        count = int(torch.cuda.device_count()) if available else 0
        if available:
            print(f"CUDA: available ({count} device(s)); torch CUDA={torch.version.cuda}")
        else:
            msg = "CUDA is not available. StyleTTS2 training/fine-tuning is CUDA-oriented."
            (errors if require_for_run and not allow_no_cuda else warnings).append(msg)
    except Exception as exc:  # pragma: no cover - import failures vary
        msg = f"CUDA check failed while importing torch: {exc}"
        (errors if require_for_run and not allow_no_cuda else warnings).append(msg)


def find_accelerate_executable() -> Optional[str]:
    """Return an accelerate executable visible from PATH or next to sys.executable."""
    found = shutil.which("accelerate")
    if found:
        return found
    sibling = Path(sys.executable).resolve().parent / "accelerate"
    if sibling.exists() and os.access(sibling, os.X_OK):
        return str(sibling)
    return None


def build_command(args: argparse.Namespace, config_arg: str) -> List[str]:
    script = STAGE_SCRIPT[args.stage]
    if args.stage == "first":
        if args.mixed_precision is not None:
            raise SystemExit("Refusing --mixed-precision for first stage; the repository warns first-stage mixed precision can cause NaNs.")
        accelerate_bin = find_accelerate_executable() or "accelerate"
        cmd = [accelerate_bin, "launch"]
        if args.num_processes is not None:
            cmd.extend(["--num_processes", str(args.num_processes)])
        cmd.extend([script, "--config_path", config_arg])
        return cmd
    if args.stage == "finetune-accelerate":
        mixed = args.mixed_precision or "fp16"
        num_processes = args.num_processes if args.num_processes is not None else 1
        accelerate_bin = find_accelerate_executable() or "accelerate"
        return [
            accelerate_bin,
            "launch",
            "--mixed_precision",
            mixed,
            "--num_processes",
            str(num_processes),
            script,
            "--config_path",
            config_arg,
        ]
    if args.num_processes is not None or args.mixed_precision is not None:
        raise SystemExit("--num-processes/--mixed-precision only apply to accelerate stages (first or finetune-accelerate).")
    return ["python", script, "--config_path", config_arg]


def preflight(args: argparse.Namespace, repo_root: Path, config_path: Path, config_arg: str) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []

    if not repo_root.exists() or not repo_root.is_dir():
        errors.append(f"Repo root is not a directory: {repo_root}")
        return warnings, errors

    script_path = repo_root / STAGE_SCRIPT[args.stage]
    check_path("Stage launcher", script_path, True, warnings, errors, expect_dir=False)
    check_path("Config", config_path, True, warnings, errors, expect_dir=False)

    config: Dict[str, Any] = {}
    if config_path.exists():
        cfg, yaml_warnings, yaml_errors = load_yaml(config_path)
        config = cfg
        warnings.extend(yaml_warnings)
        errors.extend(yaml_errors)

    check_python_imports(args.stage, warnings)

    if args.stage in {"first", "finetune-accelerate"} and find_accelerate_executable() is None:
        msg = "accelerate executable is not on PATH and was not found next to the active Python executable."
        (errors if args.run else warnings).append(msg)

    if config:
        log_dir = resolve_log_dir(repo_root, config)
        if log_dir is None:
            errors.append("Config is missing log_dir.")

        data_params = config.get("data_params") if isinstance(config.get("data_params"), dict) else {}
        if not data_params:
            errors.append("Config is missing data_params mapping.")
        else:
            for key in ["train_data", "val_data", "OOD_data"]:
                check_path(f"data_params.{key}", rel_or_abs_path(repo_root, data_params.get(key)), args.run, warnings, errors, expect_dir=False)
            root_value = data_params.get("root_path")
            if root_value in (None, ""):
                warnings.append("data_params.root_path is empty; audio rows must resolve from the training working directory or be absolute.")
            else:
                root_path = rel_or_abs_path(repo_root, str(root_value))
                if root_path is not None and not root_path.exists():
                    warnings.append(f"data_params.root_path does not exist from this environment: {root_path}")

        for key, expect_dir in [("ASR_config", False), ("ASR_path", False), ("F0_path", False), ("PLBERT_dir", True)]:
            check_path(key, rel_or_abs_path(repo_root, config.get(key)), args.run, warnings, errors, expect_dir=expect_dir)

        pretrained = str(config.get("pretrained_model") or "")
        second_stage_load_pretrained = bool(config.get("second_stage_load_pretrained", False))
        load_only_params = config.get("load_only_params", None)

        if args.stage == "first" and pretrained:
            check_path("pretrained_model", rel_or_abs_path(repo_root, pretrained), args.run, warnings, errors, expect_dir=False)

        if args.stage in {"second", "finetune", "finetune-accelerate"}:
            if pretrained and second_stage_load_pretrained:
                check_path("pretrained_model", rel_or_abs_path(repo_root, pretrained), args.run, warnings, errors, expect_dir=False)
            else:
                ckpt = resolve_first_stage_checkpoint(repo_root, config)
                check_path("log_dir/first_stage_path", ckpt, args.run, warnings, errors, expect_dir=False)
                if args.stage in {"finetune", "finetune-accelerate"}:
                    warnings.append("Fine-tuning normally expects a full second-stage pretrained checkpoint; current config will use first_stage_path fallback.")

        print("Config summary:")
        for label, value in [
            ("log_dir", config.get("log_dir")),
            ("batch_size", config.get("batch_size")),
            ("max_len", config.get("max_len")),
            ("epochs_1st", config.get("epochs_1st")),
            ("epochs_2nd", config.get("epochs_2nd")),
            ("epochs", config.get("epochs")),
            ("first_stage_path", config.get("first_stage_path")),
            ("pretrained_model", pretrained or "<empty>"),
            ("second_stage_load_pretrained", second_stage_load_pretrained),
            ("load_only_params", load_only_params),
            ("loss_params.joint_epoch", config_value(config, "loss_params.joint_epoch", "<missing>")),
            ("slmadv_params.batch_percentage", config_value(config, "slmadv_params.batch_percentage", "<missing>")),
            ("model_params.slm.model", config_value(config, "model_params.slm.model", "<missing>")),
        ]:
            print(f"  {label}: {value}")

    check_cuda(warnings, errors, require_for_run=args.run, allow_no_cuda=args.allow_no_cuda)
    return warnings, errors


def main() -> int:
    args = parse_args()
    config_arg = args.config or STAGE_DEFAULT_CONFIG[args.stage]
    repo_root = Path(args.repo_root).expanduser().resolve()
    config_path = rel_or_abs_path(repo_root, config_arg)
    if config_path is None:
        print("Internal error: config path resolved to None", file=sys.stderr)
        return 2

    try:
        command = build_command(args, config_arg)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Repo root: {repo_root}")
    print(f"Stage: {args.stage}")
    print("Command:")
    print("  " + shlex.join(command))
    print()

    warnings, errors = preflight(args, repo_root, config_path, config_arg)

    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")
        print()
    if errors:
        print("Errors:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        return 1

    if not args.run:
        print("Dry-run only: no training, downloads, or checkpoint writes were started. Add --run to execute.")
        return 0

    print("Executing training command. This may write logs/checkpoints under log_dir and may download/cache WavLM if missing.")
    completed = subprocess.run(command, cwd=str(repo_root), check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

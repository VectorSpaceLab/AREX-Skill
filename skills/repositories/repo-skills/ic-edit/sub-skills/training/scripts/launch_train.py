#!/usr/bin/env python3
"""Resolve and optionally launch the ICEdit training checkout.

The helper is deliberately safe by default: it resolves the nested training
layout and prints the exact working directory, import path, environment, and
command.  ``--execute`` performs the same preflight checks, then starts the
checkout's training module only when local inputs that are unambiguously paths
are present.  Hub model/dataset identifiers are left for the training code to
resolve online or from the Hugging Face cache.
"""

from __future__ import annotations

import argparse
import glob
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency gate
    raise SystemExit("PyYAML is required to inspect ICEdit training configs; install pyyaml.") from exc


DEFAULT_CONFIGS = {"normal": "normal_lora.yaml", "moe": "moe_lora.yaml"}
PATH_KEYS = {
    "checkpoint",
    "checkpoint_path",
    "flux_path",
    "lora",
    "lora_path",
    "model_path",
    "pretrained_model_name_or_path",
    "resume",
    "resume_from_checkpoint",
}
LOCAL_PREFIXES = {"ckpt", "checkpoint", "checkpoints", "lora", "loras", "model", "models"}
GLOB_CHARS = "*?["


def find_repo_root(start: Path) -> Path | None:
    """Find an ICEdit checkout, without making dry-run depend on one."""
    for candidate in [start] + list(start.parents):
        if (candidate / "train" / "README.md").is_file() and (
            (candidate / "train" / "src" / "train" / "train.py").is_file()
            or (candidate / "train" / "train" / "config").is_dir()
        ):
            return candidate
    return None


def resolve_train_root(repo_root: Path | None, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    if repo_root is not None:
        return (repo_root / "train").resolve()
    raise SystemExit("Cannot infer the training root; pass --repo-root or --train-root.")


def config_root(train_root: Path) -> Path:
    return train_root / "train" / "config"


def source_root(train_root: Path) -> Path:
    return train_root / "src"


def infer_train_root(config_arg: str) -> Path | None:
    """Infer ``.../train`` from an absolute ``.../train/train/config/*.yaml``."""
    raw = Path(config_arg).expanduser()
    if not raw.is_absolute():
        return None
    for parent in raw.parents:
        if parent.name == "config" and parent.parent.name == "train":
            return parent.parent.parent.resolve()
    return None


def resolve_config_path(train_root: Path, config_arg: str, mode: str) -> Path:
    """Resolve config names against the real ``train/train/config`` directory."""
    del mode  # retained in the signature for callers of the original helper
    raw = Path(config_arg).expanduser()
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        # An explicitly supplied relative path may be relative to the caller,
        # while a bare filename is always looked up in the checkout config dir.
        candidates.extend([Path.cwd() / raw, train_root / raw, config_root(train_root) / raw])
        if not raw.suffix:
            candidates.append(config_root(train_root) / f"{raw.name}.yaml")

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    if raw.is_absolute():
        return raw.resolve()
    filename = raw.name if raw.suffix else f"{raw.name}.yaml"
    return (config_root(train_root) / filename).resolve()


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"Config must parse to a mapping: {config_path}")
    return data


def warn(msg: str) -> None:
    print(f"[warn] {msg}", file=sys.stderr)


def fail(msg: str) -> None:
    raise SystemExit(f"[error] {msg}")


def _has_glob(value: str) -> bool:
    return any(char in value for char in GLOB_CHARS)


def _looks_like_local_path(value: str, key: str) -> bool:
    """Only classify clearly local references; otherwise allow Hub IDs."""
    value = value.strip()
    if not value:
        return False
    path = Path(value).expanduser()
    if path.is_absolute() or value.startswith((".", "~")) or _has_glob(value):
        return True
    if path.suffix.lower() in {".bin", ".ckpt", ".pth", ".pt", ".safetensors", ".yaml", ".yml", ".parquet"}:
        return True
    first = value.replace("\\", "/").split("/", 1)[0].lower()
    # Relative checkpoint/model folders are common in the shipped configs.
    # A value such as org/model is intentionally not considered local.
    if first in LOCAL_PREFIXES or first == "parquet":
        return True
    if "path" in key.lower() and "/" not in value and key.lower() != "flux_path":
        return True
    return False


def _resolve_local_path(value: str, train_root: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (train_root / path).resolve()


def _iter_path_settings(cfg: Dict[str, Any]) -> Iterable[tuple[str, str]]:
    def visit(mapping: Dict[str, Any], prefix: str = "") -> Iterable[tuple[str, str]]:
        for key, value in mapping.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            key_lower = str(key).lower()
            if isinstance(value, dict):
                # lora_config contains numeric settings, not a LoRA path.
                if key_lower != "lora_config":
                    yield from visit(value, name)
            elif isinstance(value, str) and key_lower in PATH_KEYS:
                yield name, value

    yield from visit(cfg)


def _missing_local_resources(cfg: Dict[str, Any], train_root: Path) -> list[str]:
    missing: list[str] = []
    dataset = cfg.get("train", {}).get("dataset", {})
    if isinstance(dataset, dict):
        dataset_type = dataset.get("type")
        dataset_value = dataset.get("path")
        if (
            dataset_type in {"edit_with_omini", "omini"}
            and isinstance(dataset_value, str)
            and _looks_like_local_path(dataset_value, "dataset.path")
        ):
            resolved = _resolve_local_path(dataset_value, train_root)
            matches = [Path(item) for item in glob.glob(str(resolved), recursive=True)]
            if not any(item.is_file() for item in matches):
                missing.append(f"local dataset {dataset_value!r} (resolved from {train_root})")

    for key, value in _iter_path_settings(cfg):
        if not _looks_like_local_path(value, key):
            continue
        resolved = _resolve_local_path(value, train_root)
        if not resolved.exists():
            missing.append(f"local {key} {value!r} (resolved as {resolved})")
    return missing


def validate_config(cfg: Dict[str, Any], config_path: Path, train_root: Path) -> list[str]:
    """Validate YAML and return local resources missing at execute time."""
    if "train" not in cfg:
        fail(f"Missing required key 'train' in {config_path}")
    train_cfg = cfg["train"]
    if not isinstance(train_cfg, dict):
        fail(f"'train' must be a mapping in {config_path}")
    if "dataset" not in train_cfg:
        fail(f"Missing required key 'train.dataset' in {config_path}")
    if not isinstance(train_cfg["dataset"], dict):
        fail(f"'train.dataset' must be a mapping in {config_path}")

    dataset_cfg = train_cfg["dataset"]
    dataset_type = dataset_cfg.get("type")
    if dataset_type not in {"edit", "omini", "edit_with_omini"}:
        fail(
            f"Unsupported train.dataset.type={dataset_type!r}; "
            "the training code supports edit, omini, and edit_with_omini"
        )
    if dataset_type in {"omini", "edit_with_omini"} and not dataset_cfg.get("path"):
        fail(f"Missing required key 'train.dataset.path' for dataset.type={dataset_type!r} in {config_path}")

    missing = [key for key in ("flux_path", "dtype") if key not in cfg]
    if missing:
        fail(f"Missing required top-level keys {missing} in {config_path}")
    for key in ("lora_config", "optimizer"):
        if key not in train_cfg:
            fail(f"Missing required key 'train.{key}' in {config_path}")

    for ignored_key in ("condition_type", "image_size", "padding", "drop_image_prob", "specific_task"):
        if ignored_key in dataset_cfg:
            warn(f"'{ignored_key}' is present in the YAML but the current train.py path does not consume it")
    if "condition_type" in train_cfg:
        warn("'train.condition_type' is not read by the current training code")

    missing_resources = _missing_local_resources(cfg, train_root)
    for resource in missing_resources:
        warn(f"Missing {resource}; dry-run remains available, but --execute will refuse to launch")

    if "wandb" in train_cfg and not os.environ.get("WANDB_API_KEY"):
        warn("WANDB_API_KEY is missing; wandb init will be skipped but training can continue")
    if cfg.get("use_offset_noise") not in (None, True, False):
        warn("use_offset_noise should be a boolean when present")
    if cfg.get("dtype") == "bfloat16" and os.environ.get("CUDA_VISIBLE_DEVICES") == "":
        warn("CUDA_VISIBLE_DEVICES is empty; the launcher will not have a visible device to bind")
    return missing_resources


def checkout_requirements(train_root: Path, repo_root: Path | None, mode: str) -> list[str]:
    issues: list[str] = []
    expected_source = source_root(train_root) / "train" / ("train_moe.py" if mode == "moe" else "train.py")
    if not expected_source.is_file():
        issues.append(f"checkout training source is absent: {expected_source}")
    if mode == "moe":
        vendored = (repo_root / "icedit") if repo_root is not None else None
        if vendored is None or not vendored.is_dir():
            issues.append("MoE launch requires the checkout-vendored icedit/ package; it is not part of this helper")
    return issues


def build_command(mode: str, port: int = 41353) -> list[str]:
    entrypoint = "src.train.train_moe" if mode == "moe" else "src.train.train"
    return ["accelerate", "launch", "--main_process_port", str(port), "-m", entrypoint]


def build_environment(
    train_root: Path,
    config_path: Path,
    cuda: str,
    mode: str = "normal",
    repo_root: Path | None = None,
) -> dict[str, str]:
    # The checkout wrappers run from <checkout>/train with PYTHONPATH=.;
    # train_moe.py also prepends the vendored fork itself. Keep that source
    # contract explicit in the environment and dry-run output.
    pythonpath = [str(train_root)]
    if mode == "moe" and repo_root is not None:
        vendored = repo_root / "icedit"
        if vendored.is_dir():
            pythonpath.append(str(vendored))
    existing = os.environ.get("PYTHONPATH")
    if existing:
        pythonpath.append(existing)
    return {
        "XFL_CONFIG": str(config_path),
        "TOKENIZERS_PARALLELISM": "true",
        "PYTHONPATH": os.pathsep.join(pythonpath),
        "CUDA_VISIBLE_DEVICES": cuda,
    }


def print_summary(
    train_root: Path,
    config_path: Path,
    cfg: Dict[str, Any],
    command: list[str],
    cuda: str,
    mode: str,
    repo_root: Path | None = None,
) -> None:
    env = build_environment(train_root, config_path, cuda, mode, repo_root)
    print("ICEdit training dry-run")
    print(f"  repo root:    {train_root.parent}")
    print(f"  train root:   {train_root}")
    print(f"  source root:  {source_root(train_root)}")
    print(f"  config root:  {config_root(train_root)}")
    print(f"  config:       {config_path}")
    print(f"  cwd:          {train_root}")
    print(f"  mode:         {mode}")
    if mode == "moe" and repo_root is not None:
        print(f"  vendored icedit: {repo_root / 'icedit'}")
    print(f"  entrypoint:   {command[-1]}")
    print("  env:")
    for key, value in env.items():
        print(f"    {key}={value}")
    print("  command:")
    print("   ", " ".join(shlex.quote(part) for part in command))
    print()
    print("Resolved config keys:")
    print(f"  flux_path: {cfg.get('flux_path')}")
    print(f"  dtype:     {cfg.get('dtype')}")
    print(f"  dataset:   {cfg.get('train', {}).get('dataset', {}).get('type')}")
    print(f"  save_path: {cfg.get('train', {}).get('save_path', 'runs')}")


def execute(
    train_root: Path,
    config_path: Path,
    command: list[str],
    cuda: str = "2",
    mode: str = "normal",
    repo_root: Path | None = None,
) -> int:
    env = os.environ.copy()
    env.update(build_environment(train_root, config_path, cuda, mode, repo_root))
    print("Launching training job...", file=sys.stderr)
    completed = subprocess.run(command, cwd=train_root, env=env)
    return completed.returncode

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or launch ICEdit training.")
    parser.add_argument("--mode", choices=["normal", "moe"], default="normal")
    parser.add_argument(
        "--config",
        default=None,
        help="Config filename or path. Defaults to normal_lora.yaml or moe_lora.yaml in train/train/config.",
    )
    parser.add_argument("--port", type=int, default=41353, help="Accelerate main-process port.")
    parser.add_argument(
        "--cuda", default=os.environ.get("CUDA_VISIBLE_DEVICES", "2"), help="CUDA_VISIBLE_DEVICES mapping."
    )
    parser.add_argument("--repo-root", default=None, help="Override the ICEdit checkout root.")
    parser.add_argument(
        "--train-root", default=None, help="Override the training working root (the directory used as cwd)."
    )
    parser.add_argument(
        "--execute", action="store_true", help="Run accelerate launch after all preflight checks pass."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    global ARGS
    ARGS = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    repo_root = Path(ARGS.repo_root).expanduser().resolve() if ARGS.repo_root else find_repo_root(script_dir)

    if repo_root is None and ARGS.config:
        inferred = infer_train_root(ARGS.config)
        if inferred is not None:
            repo_root = inferred.parent
    if repo_root is None and ARGS.train_root:
        repo_root = Path(ARGS.train_root).expanduser().resolve().parent
    if repo_root is None:
        warn("No ICEdit checkout discovered; this standalone helper can still dry-run with explicit paths")

    train_root = resolve_train_root(repo_root, ARGS.train_root)
    config_arg = ARGS.config or DEFAULT_CONFIGS[ARGS.mode]
    config_path = resolve_config_path(train_root, config_arg, ARGS.mode)
    if not config_path.is_file():
        fail(f"Config file does not exist: {config_path}")

    cfg = load_config(config_path)
    missing_resources = validate_config(cfg, config_path, train_root)
    checkout_issues = checkout_requirements(train_root, repo_root, ARGS.mode)
    for issue in checkout_issues:
        warn(f"{issue}; dry-run remains available")

    command = build_command(ARGS.mode, ARGS.port)
    if not ARGS.execute:
        print_summary(train_root, config_path, cfg, command, ARGS.cuda, ARGS.mode, repo_root)
        print("\nDry-run only. Re-run with --execute to start the GPU job.")
        return 0

    blocking = missing_resources + checkout_issues
    if blocking:
        fail("Refusing --execute before subprocess: " + "; ".join(blocking))
    return execute(train_root, config_path, command, ARGS.cuda, ARGS.mode, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())

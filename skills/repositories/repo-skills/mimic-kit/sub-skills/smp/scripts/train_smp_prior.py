#!/usr/bin/env python3
"""Run or dry-check MimicKit TinyMDM/SMP prior training from an explicit checkout.

This generated-skill helper is a safe wrapper around the target checkout's
``tools/diffusion_model/train_tinymdm.py``. Use ``--dry-run-config`` to validate
imports, config paths, and common asset gaps without launching training or
sampling.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - reported at runtime
    raise SystemExit(f"Missing dependency PyYAML: {exc}")

EXTERNAL_ASSET_PREFIXES = (
    "data/motions/",
    "data/models/",
    "data/logs/",
    "data/assets/objects/",
    "output/",
)


def add_repo_paths(repo_root: Path) -> None:
    for candidate in (repo_root / "tools" / "diffusion_model", repo_root / "mimickit", repo_root):
        text = str(candidate)
        if candidate.exists() and text not in sys.path:
            sys.path.insert(0, text)


def resolve_path(repo_root: Path, raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def rel_for_report(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file did not contain a mapping: {path}")
    return data


def is_external_missing(repo_root: Path, path: Path) -> bool:
    rel = rel_for_report(repo_root, path)
    return any(rel.startswith(prefix) for prefix in EXTERNAL_ASSET_PREFIXES)


def check_motion_source(repo_root: Path, motion_path: Path, warnings: list[str], errors: list[str]) -> None:
    rel = rel_for_report(repo_root, motion_path)
    if not motion_path.exists():
        if is_external_missing(repo_root, motion_path) or rel.startswith("data/datasets/"):
            warnings.append(f"motion source is missing or not downloaded yet: {rel}")
        else:
            errors.append(f"motion source does not exist: {rel}")
        return

    if motion_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            dataset = load_yaml(motion_path)
            entries = dataset.get("motions", [])
            if not isinstance(entries, list):
                errors.append(f"dataset motions field is not a list: {rel}")
                return
            missing = []
            for entry in entries:
                if not isinstance(entry, dict) or "file" not in entry:
                    errors.append(f"dataset entry missing file field in {rel}")
                    continue
                item = resolve_path(repo_root, str(entry["file"]))
                if not item.exists():
                    missing.append(rel_for_report(repo_root, item))
            if missing:
                sample = ", ".join(missing[:5])
                suffix = "" if len(missing) <= 5 else f" ... +{len(missing) - 5} more"
                warnings.append(f"dataset manifest exists but referenced motion files are missing: {sample}{suffix}")
        except Exception as exc:
            errors.append(f"failed to parse dataset manifest {rel}: {exc}")


def dry_run_config(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not repo_root.is_dir():
        errors.append(f"repo root is not a directory: {repo_root}")
    else:
        add_repo_paths(repo_root)

    # Import the target trainer without launching training.
    imported = False
    if not errors:
        try:
            importlib.import_module("train_tinymdm")
            importlib.import_module("motion_prior_dataset")
            importlib.import_module("learning.tinymdm.tinymdm_model")
            imported = True
        except Exception as exc:
            errors.append(f"failed to import target TinyMDM modules: {type(exc).__name__}: {exc}")

    cfg_path = resolve_path(repo_root, args.cfg_path)
    cfg: dict[str, Any] = {}
    if not cfg_path.is_file():
        errors.append(f"prior config does not exist: {rel_for_report(repo_root, cfg_path)}")
    else:
        try:
            cfg = load_yaml(cfg_path)
        except Exception as exc:
            errors.append(f"failed to load prior config: {exc}")

    required = ["env_config", "motion_file", "control_freq", "T", "loss_type", "estimate_mode", "noise_schedule_mode", "batch_size", "num_iterations"]
    for key in required:
        if cfg and key not in cfg:
            errors.append(f"prior config missing required field: {key}")

    env_config: dict[str, Any] = {}
    env_path = None
    if cfg.get("env_config"):
        env_path = resolve_path(repo_root, str(cfg["env_config"]))
        if not env_path.is_file():
            errors.append(f"env config does not exist: {rel_for_report(repo_root, env_path)}")
        else:
            try:
                env_config = load_yaml(env_path)
            except Exception as exc:
                errors.append(f"failed to load env config: {exc}")

    if cfg.get("motion_file"):
        check_motion_source(repo_root, resolve_path(repo_root, str(cfg["motion_file"])), warnings, errors)

    if env_config.get("char_file"):
        char_path = resolve_path(repo_root, str(env_config["char_file"]))
        if not char_path.exists():
            errors.append(f"character asset does not exist: {rel_for_report(repo_root, char_path)}")

    if args.mode == "test":
        if not args.model_file:
            errors.append("--mode test requires --model_file")
        else:
            model_path = resolve_path(repo_root, args.model_file)
            if not model_path.is_file():
                if is_external_missing(repo_root, model_path):
                    warnings.append(f"prior model file is not present yet: {rel_for_report(repo_root, model_path)}")
                else:
                    errors.append(f"prior model file does not exist: {rel_for_report(repo_root, model_path)}")

    summary = {
        "ok": not errors,
        "repo_root": str(repo_root),
        "cfg_path": rel_for_report(repo_root, cfg_path),
        "mode": args.mode,
        "imports_ok": imported,
        "env_config": rel_for_report(repo_root, env_path) if env_path else None,
        "motion_file": cfg.get("motion_file"),
        "control_freq": cfg.get("control_freq"),
        "device": args.device,
        "warnings": warnings,
        "errors": errors,
    }
    return summary, 0 if not errors else 1


def run_target(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    add_repo_paths(repo_root)
    os.chdir(repo_root)
    module = importlib.import_module("train_tinymdm")
    cfg_path = str(resolve_path(repo_root, args.cfg_path))
    if args.mode == "train":
        module.train(cfg_path, out_dir=args.out_dir, device=args.device)
    else:
        module.test(cfg_path, args.model_file, out_dir=args.out_dir, num_samples=args.num_samples, device=args.device)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-check or run MimicKit TinyMDM prior training/testing from a target checkout.")
    parser.add_argument("--repo-root", required=True, help="Target MimicKit checkout root")
    parser.add_argument("--mode", default="train", choices=["train", "test"], help="Prior workflow mode")
    parser.add_argument("--cfg_path", default="tools/diffusion_model/config/tinymdm_multi_clip.yaml", help="Prior config path, relative to repo root unless absolute")
    parser.add_argument("--out_dir", required=True, help="Output directory passed through to the target trainer")
    parser.add_argument("--model_file", default="", help="Prior model checkpoint for --mode test")
    parser.add_argument("--device", default="cuda", help="Torch device string, for example cuda or cpu")
    parser.add_argument("--num-samples", type=int, default=16, help="Number of samples for --mode test")
    parser.add_argument("--dry-run-config", action="store_true", help="Validate imports/config/assets without training or sampling")
    parser.add_argument("--json", action="store_true", help="Print dry-run summary as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.dry_run_config:
        summary, code = dry_run_config(args)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print("MimicKit SMP prior dry run")
            print(f"status: {'OK' if summary['ok'] else 'FAIL'}")
            print(f"cfg_path: {summary['cfg_path']}")
            print(f"env_config: {summary['env_config']}")
            print(f"motion_file: {summary['motion_file']}")
            print(f"imports_ok: {summary['imports_ok']}")
            for item in summary["warnings"]:
                print(f"warning: {item}")
            for item in summary["errors"]:
                print(f"error: {item}")
        return code
    return run_target(args)


if __name__ == "__main__":
    raise SystemExit(main())

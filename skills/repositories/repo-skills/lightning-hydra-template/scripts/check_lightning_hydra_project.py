#!/usr/bin/env python3
"""Inspect a Lightning-Hydra-Template checkout without running training.

Examples:
  python check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
  python check_lightning_hydra_project.py --repo-root . --config-name eval.yaml --override ckpt_path=/tmp/dummy.ckpt --instantiate
  python check_lightning_hydra_project.py --repo-root . --cuda-probe

The script composes Hydra configs and optionally instantiates configured objects.
It does not call DataModule.prepare_data(), Trainer.fit(), or Trainer.test().
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from importlib.metadata import PackageNotFoundError, entry_points, version
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Target project root to inspect.")
    parser.add_argument("--config-name", default="train.yaml", help="Hydra config name under <repo-root>/configs.")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override; repeat for multiple overrides, e.g. --override trainer=cpu.",
    )
    parser.add_argument("--instantiate", action="store_true", help="Instantiate cfg.data, cfg.model, and cfg.trainer when present.")
    parser.add_argument("--check-cli", action="store_true", help="Check train_command/eval_command entry points.")
    parser.add_argument("--cuda-probe", action="store_true", help="Run a tiny torch CUDA availability probe if torch imports.")
    return parser.parse_args()


def require_files(root: Path) -> None:
    required = ["configs", "src", "tests", "setup.py"]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise SystemExit(f"Missing expected template paths under {root}: {', '.join(missing)}")


def import_required_modules() -> None:
    modules = ["hydra", "omegaconf", "lightning", "torch", "src.train", "src.eval"]
    for module in modules:
        try:
            imported = importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - diagnostics should preserve exception text
            raise SystemExit(f"Failed to import {module}: {exc}") from exc
        print(f"import ok: {module} -> {getattr(imported, '__file__', 'builtin')}")


def print_distribution_and_entry_points(check_cli: bool) -> None:
    for dist in ["src", "lightning", "hydra-core", "torch", "torchvision", "torchmetrics", "rootutils"]:
        try:
            print(f"dist: {dist}=={version(dist)}")
        except PackageNotFoundError:
            print(f"dist missing: {dist}")
    if check_cli:
        eps = {ep.name: ep.value for ep in entry_points(group="console_scripts") if ep.name in {"train_command", "eval_command"}}
        print(f"console_scripts: {eps}")
        missing = {"train_command", "eval_command"} - set(eps)
        if missing:
            raise SystemExit(f"Missing console scripts: {sorted(missing)}")


def compose_config(root: Path, config_name: str, overrides: Iterable[str], instantiate: bool) -> None:
    from hydra import compose, initialize_config_dir
    from hydra.core.global_hydra import GlobalHydra
    from hydra.utils import instantiate as hydra_instantiate
    from omegaconf import OmegaConf, open_dict

    config_dir = root / "configs"
    if not config_dir.is_dir():
        raise SystemExit(f"Config directory not found: {config_dir}")

    GlobalHydra.instance().clear()
    with initialize_config_dir(version_base="1.3", config_dir=str(config_dir.resolve())):
        cfg = compose(config_name=config_name, return_hydra_config=True, overrides=list(overrides))
        with open_dict(cfg):
            cfg.paths.root_dir = str(root.resolve())
            cfg.paths.output_dir = str(root.resolve() / "_skill_smoke_output")
            cfg.paths.log_dir = str(root.resolve() / "_skill_smoke_logs")
            if cfg.get("extras"):
                cfg.extras.print_config = False
                cfg.extras.enforce_tags = False
            if "logger" in cfg:
                cfg.logger = None
        print("composed config:", config_name)
        print("top-level keys:", sorted(str(k) for k in cfg.keys())[:30])
        print("data target:", cfg.get("data", {}).get("_target_", None))
        print("model target:", cfg.get("model", {}).get("_target_", None))
        print("trainer target:", cfg.get("trainer", {}).get("_target_", None))
        if instantiate:
            for key in ["data", "model", "trainer"]:
                if cfg.get(key) is None:
                    continue
                obj = hydra_instantiate(cfg[key])
                print(f"instantiated {key}: {type(obj).__module__}.{type(obj).__name__}")
        if config_name.startswith("eval") and "ckpt_path" in cfg:
            print("eval ckpt_path:", OmegaConf.to_container(cfg).get("ckpt_path"))


def cuda_probe() -> None:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        print(f"cuda probe skipped: torch import failed: {exc}")
        return
    print("torch:", torch.__version__, "cuda runtime:", torch.version.cuda)
    print("cuda available:", torch.cuda.is_available(), "device_count:", torch.cuda.device_count())
    if torch.cuda.is_available():
        print("cuda device 0:", torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
        torch.empty((1,), device="cuda")
        print("cuda tensor smoke: passed")


def main() -> None:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("PROJECT_ROOT", str(root))
    require_files(root)
    print_distribution_and_entry_points(args.check_cli)
    import_required_modules()
    compose_config(root, args.config_name, args.override, args.instantiate)
    if args.cuda_probe:
        cuda_probe()


if __name__ == "__main__":
    main()

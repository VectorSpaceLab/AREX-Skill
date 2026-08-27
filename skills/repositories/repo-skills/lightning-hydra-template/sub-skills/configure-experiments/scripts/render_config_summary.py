#!/usr/bin/env python3
"""Compose and summarize a Lightning-Hydra-Template config without training."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Target project root.")
    parser.add_argument("--config-name", default="train.yaml", help="Config file under configs/, e.g. train.yaml or eval.yaml.")
    parser.add_argument("--override", action="append", default=[], help="Hydra override; repeat as needed.")
    parser.add_argument("--resolve", action="store_true", help="Resolve OmegaConf interpolations in printed YAML.")
    parser.add_argument("--list-groups", action="store_true", help="List immediate options in each configs/ group directory.")
    parser.add_argument("--print-yaml", action="store_true", help="Print the composed YAML instead of only a summary.")
    return parser.parse_args()


def list_groups(config_dir: Path) -> None:
    for child in sorted(config_dir.iterdir()):
        if child.is_dir() and not child.name.startswith("__"):
            opts = sorted(p.stem for p in child.glob("*.yaml"))
            print(f"{child.name}: {', '.join(opts) if opts else '(no yaml options)'}")


def main() -> None:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    config_dir = root / "configs"
    if not config_dir.is_dir():
        raise SystemExit(f"No configs/ directory under {root}")
    sys.path.insert(0, str(root))
    os.environ.setdefault("PROJECT_ROOT", str(root))

    if args.list_groups:
        list_groups(config_dir)

    try:
        from hydra import compose, initialize_config_dir
        from hydra.core.global_hydra import GlobalHydra
        from omegaconf import OmegaConf, open_dict
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Hydra/OmegaConf import failed; install project requirements first: {exc}") from exc

    GlobalHydra.instance().clear()
    with initialize_config_dir(version_base="1.3", config_dir=str(config_dir)):
        cfg = compose(config_name=args.config_name, return_hydra_config=True, overrides=args.override)
        with open_dict(cfg):
            if cfg.get("paths"):
                cfg.paths.root_dir = str(root)
                cfg.paths.output_dir = str(root / "_skill_smoke_output")
                cfg.paths.log_dir = str(root / "_skill_smoke_logs")
            if cfg.get("extras"):
                cfg.extras.print_config = False
                cfg.extras.enforce_tags = False
        print(f"composed: {args.config_name}")
        print("overrides:", args.override)
        for key in ["task_name", "tags", "ckpt_path", "optimized_metric"]:
            if key in cfg:
                print(f"{key}: {cfg[key]}")
        for key in ["data", "model", "trainer", "callbacks", "logger", "debug", "hparams_search"]:
            if key in cfg and cfg[key] is not None:
                target = cfg[key].get("_target_") if hasattr(cfg[key], "get") else None
                print(f"{key}: target={target} type={type(cfg[key]).__name__}")
        if args.print_yaml:
            print(OmegaConf.to_yaml(cfg, resolve=args.resolve))


if __name__ == "__main__":
    main()

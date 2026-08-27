#!/usr/bin/env python3
"""Summarize a StarVLA YAML config without launching training or loading weights."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a StarVLA YAML config and optional KEY=VALUE overrides.")
    parser.add_argument("config_yaml", type=Path, help="Path to a StarVLA YAML config file.")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Dotlist override to summarize. May be repeated. This script validates shape but does not merge complex values.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser.parse_args(argv)


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required to inspect configs. Install pyyaml or use a StarVLA environment with YAML support.")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError:
        raise SystemExit(f"Config not found: {path}")
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid YAML in {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Expected top-level YAML mapping in {path}")
    return data


def get_path(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def validate_overrides(overrides: list[str]) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for item in overrides:
        if "=" not in item or item.startswith("="):
            raise SystemExit(f"Invalid override {item!r}; expected KEY=VALUE.")
        key, value = item.split("=", 1)
        if not key.strip():
            raise SystemExit(f"Invalid override {item!r}; key is empty.")
        parsed.append({"key": key.strip(), "value": value})
    return parsed


def summarize(cfg: dict[str, Any], overrides: list[dict[str, str]]) -> dict[str, Any]:
    framework = get_path(cfg, "framework") or {}
    action_model = get_path(cfg, "framework.action_model") or {}
    datasets = get_path(cfg, "datasets") or {}
    trainer = get_path(cfg, "trainer") or {}
    summary = {
        "run": {
            "run_id": cfg.get("run_id"),
            "run_root_dir": cfg.get("run_root_dir"),
            "output_dir": cfg.get("output_dir"),
            "seed": cfg.get("seed"),
        },
        "framework": {
            "name": framework.get("name") if isinstance(framework, dict) else None,
            "base_vlm": get_path(cfg, "framework.qwenvl.base_vlm"),
            "base_world_model": get_path(cfg, "framework.world_model.base_wm") or get_path(cfg, "framework.wm.base_wm"),
            "action_dim": action_model.get("action_dim") if isinstance(action_model, dict) else None,
            "state_dim": action_model.get("state_dim") if isinstance(action_model, dict) else None,
            "action_horizon": action_model.get("action_horizon") if isinstance(action_model, dict) else None,
            "future_action_window_size": action_model.get("future_action_window_size") if isinstance(action_model, dict) else None,
        },
        "datasets": {},
        "trainer": {
            "max_train_steps": trainer.get("max_train_steps") if isinstance(trainer, dict) else None,
            "save_interval": trainer.get("save_interval") if isinstance(trainer, dict) else None,
            "eval_interval": trainer.get("eval_interval") if isinstance(trainer, dict) else None,
            "freeze_modules": trainer.get("freeze_modules") if isinstance(trainer, dict) else None,
            "learning_rate": trainer.get("learning_rate") if isinstance(trainer, dict) else None,
            "loss_scale": trainer.get("loss_scale") if isinstance(trainer, dict) else None,
        },
        "overrides": overrides,
        "warnings": [],
    }

    if isinstance(datasets, dict):
        for key, value in datasets.items():
            if isinstance(value, dict):
                summary["datasets"][key] = {
                    "dataset_py": value.get("dataset_py"),
                    "data_root_dir": value.get("data_root_dir"),
                    "data_mix": value.get("data_mix"),
                    "per_device_batch_size": value.get("per_device_batch_size"),
                    "obs_image_size": value.get("obs_image_size") or value.get("image_size"),
                    "action_type": value.get("action_type"),
                }

    horizon = summary["framework"].get("action_horizon")
    future = summary["framework"].get("future_action_window_size")
    if horizon is None and future is not None:
        summary["warnings"].append("action chunk size is likely future_action_window_size + 1; deployment code handles this compatibility style.")
    if summary["framework"].get("name") is None:
        summary["warnings"].append("framework.name is missing; current StarVLA framework construction expects it.")
    if not summary["datasets"]:
        summary["warnings"].append("No datasets section was summarized; training entry points usually require datasets.vla_data and/or datasets.vlm_data.")
    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    overrides = validate_overrides(args.override)
    cfg = load_yaml(args.config_yaml)
    summary = summarize(cfg, overrides)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("StarVLA config summary")
        print(f"framework.name: {summary['framework']['name']}")
        print(f"action_dim/state_dim: {summary['framework']['action_dim']} / {summary['framework']['state_dim']}")
        print(f"action_horizon: {summary['framework']['action_horizon']}")
        print("datasets:")
        for name, ds in summary["datasets"].items():
            print(f"  {name}: dataset_py={ds['dataset_py']} data_mix={ds['data_mix']} root={ds['data_root_dir']}")
        print(f"trainer.max_train_steps: {summary['trainer']['max_train_steps']}")
        if overrides:
            print("overrides:")
            for item in overrides:
                print(f"  {item['key']}={item['value']}")
        for warning in summary["warnings"]:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

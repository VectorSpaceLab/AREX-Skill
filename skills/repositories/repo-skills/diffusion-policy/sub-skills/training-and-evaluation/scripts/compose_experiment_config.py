#!/usr/bin/env python3
"""Safely compose a Diffusion Policy Hydra experiment config.

This helper inspects config structure only. It never instantiates workspaces,
starts training, launches Ray, imports W&B, or touches datasets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

try:  # Optional: full Hydra/OmegaConf composition when installed.
    import hydra  # type: ignore
    from omegaconf import OmegaConf  # type: ignore

    HYDRA_AVAILABLE = True
except Exception:  # pragma: no cover - depends on runtime environment.
    hydra = None  # type: ignore
    OmegaConf = None  # type: ignore
    HYDRA_AVAILABLE = False

try:
    import yaml  # type: ignore

    YAML_AVAILABLE = True
except Exception:  # pragma: no cover - depends on runtime environment.
    yaml = None  # type: ignore
    YAML_AVAILABLE = False


SELECTED_PATHS = (
    "name",
    "task.name",
    "task.dataset_path",
    "task.dataset.zarr_path",
    "task.dataset._target_",
    "task.env_runner._target_",
    "policy._target_",
    "training.device",
    "training.seed",
    "logging.mode",
    "checkpoint.topk.monitor_key",
    "hydra.run.dir",
    "multi_run.run_dir",
)


def normalize_config_name(name: str) -> str:
    return name[:-5] if name.endswith(".yaml") else name


def load_yaml(path: Path) -> Dict[str, Any]:
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML is required for the fallback config loader")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)  # type: ignore[union-attr]
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping YAML at {path}")
    return data


def parse_override_value(value: str) -> Any:
    if not YAML_AVAILABLE:
        return value
    try:
        parsed = yaml.safe_load(value)  # type: ignore[union-attr]
    except Exception:
        return value
    return "" if parsed is None and value == "" else parsed


def task_config_path(config_root: Path, task_name: str) -> Path:
    return config_root / "task" / f"{normalize_config_name(task_name)}.yaml"


def load_task_config(config_root: Path, task_name: str) -> Dict[str, Any]:
    path = task_config_path(config_root, task_name)
    if not path.is_file():
        raise FileNotFoundError(f"task config not found: {path}")
    return load_yaml(path)


def default_task_from_defaults(defaults: Any) -> str | None:
    if not isinstance(defaults, list):
        return None
    for item in defaults:
        if isinstance(item, dict) and "task" in item:
            value = item["task"]
            if isinstance(value, str):
                return value
    return None


def apply_dotted_override(cfg: Dict[str, Any], key: str, value: Any) -> None:
    if key.startswith("+"):
        key = key[1:]
    if key.startswith("~"):
        # Minimal fallback: deletion overrides are Hydra-specific. Leave a marker.
        key = key[1:]
        parts = [p for p in key.split(".") if p]
        node: Dict[str, Any] = cfg
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                return
            node = child
        if parts:
            node.pop(parts[-1], None)
        return

    parts = [p for p in key.split(".") if p]
    if not parts:
        return
    node: Dict[str, Any] = cfg
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    node[parts[-1]] = value


def fallback_compose(config_root: Path, config_name: str, overrides: Sequence[str]) -> Tuple[Dict[str, Any], List[str]]:
    """Small YAML fallback for environments without Hydra.

    It supports this repo's simple `defaults: [{task: ...}]` pattern and dotted
    `key=value` overrides. Interpolations remain unresolved.
    """

    warnings: List[str] = [
        "Hydra/OmegaConf not available; using partial YAML fallback with unresolved interpolations."
    ]
    cfg_path = config_root / f"{normalize_config_name(config_name)}.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"workspace config not found: {cfg_path}")

    cfg = load_yaml(cfg_path)
    defaults = cfg.pop("defaults", [])
    default_task = default_task_from_defaults(defaults)
    if default_task is not None:
        try:
            cfg["task"] = load_task_config(config_root, default_task)
        except FileNotFoundError as exc:
            warnings.append(str(exc))

    for override in overrides:
        if "=" not in override:
            warnings.append(f"Skipping override without '=': {override}")
            continue
        key, value_text = override.split("=", 1)
        key = key.strip()
        value = parse_override_value(value_text)
        if key == "task" and isinstance(value, str):
            path = task_config_path(config_root, value)
            if path.is_file():
                cfg["task"] = load_task_config(config_root, value)
            else:
                cfg["task"] = value
                warnings.append(f"Task override did not resolve to a config file: {value}")
        else:
            apply_dotted_override(cfg, key, value)

    return cfg, warnings


def safe_eval_expression(expr: str) -> Any:
    """Restricted resolver for this repo's arithmetic/conditional ${eval:...} usage."""

    allowed_globals = {"__builtins__": {}}
    allowed_locals = {"None": None, "True": True, "False": False}
    return eval(expr, allowed_globals, allowed_locals)


def hydra_compose(config_root: Path, config_name: str, overrides: Sequence[str], resolve: bool) -> Dict[str, Any]:
    if not HYDRA_AVAILABLE:
        raise RuntimeError("Hydra/OmegaConf unavailable")
    if resolve:
        try:
            OmegaConf.register_new_resolver("eval", safe_eval_expression, replace=True)  # type: ignore[union-attr]
        except Exception:
            pass
    with hydra.initialize_config_dir(version_base=None, config_dir=str(config_root)):  # type: ignore[union-attr]
        cfg = hydra.compose(  # type: ignore[union-attr]
            config_name=normalize_config_name(config_name),
            overrides=list(overrides),
        )
    return OmegaConf.to_container(cfg, resolve=resolve, enum_to_str=True)  # type: ignore[union-attr]


def get_path(node: Any, dotted: str) -> Any:
    current = node
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return "<missing>"
    return current


def collect_targets(node: Any, path: Tuple[str, ...] = ()) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    if isinstance(node, dict):
        target = node.get("_target_")
        if isinstance(target, str):
            found.append((".".join(path + ("_target_",)), target))
        for key in sorted(node.keys()):
            if key == "_target_":
                continue
            found.extend(collect_targets(node[key], path + (str(key),)))
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            found.extend(collect_targets(item, path + (str(idx),)))
    return found


def print_targets(cfg: Dict[str, Any], mode: str, config_root: Path, config_name: str, overrides: Sequence[str], warnings: Sequence[str]) -> None:
    print(f"compose_mode: {mode}")
    print(f"config_root: {config_root}")
    print(f"config_name: {normalize_config_name(config_name)}")
    if overrides:
        print("overrides:")
        for override in overrides:
            print(f"  - {override}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print("selected_values:")
    for path in SELECTED_PATHS:
        value = get_path(cfg, path)
        print(f"  {path}: {value}")
    print("targets:")
    targets = collect_targets(cfg)
    if not targets:
        print("  <none>")
    else:
        for path, target in targets:
            print(f"  {path}: {target}")


def dump_config(cfg: Dict[str, Any]) -> None:
    if YAML_AVAILABLE:
        print(yaml.safe_dump(cfg, sort_keys=False))  # type: ignore[union-attr]
    else:
        print(json.dumps(cfg, indent=2, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compose a Diffusion Policy experiment config without starting training.",
    )
    parser.add_argument(
        "--config-root",
        default="diffusion_policy/config",
        help="Config directory to compose from (default: diffusion_policy/config).",
    )
    parser.add_argument(
        "--config-name",
        required=True,
        help="Workspace config name, with or without .yaml suffix.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Hydra override to apply. Repeat for multiple overrides.",
    )
    parser.add_argument(
        "--print-targets",
        action="store_true",
        help="Print target class paths and selected diagnostics instead of the full config.",
    )
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="Resolve OmegaConf interpolations when Hydra/OmegaConf are available. Default leaves interpolations unresolved.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_root = Path(args.config_root).expanduser().resolve()
    if not config_root.is_dir():
        print(f"error: config root not found: {config_root}", file=sys.stderr)
        return 2

    warnings: List[str] = []
    mode = "hydra"
    try:
        if HYDRA_AVAILABLE:
            cfg = hydra_compose(config_root, args.config_name, args.override, args.resolve)
        else:
            mode = "yaml-fallback"
            cfg, warnings = fallback_compose(config_root, args.config_name, args.override)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.print_targets:
        print_targets(cfg, mode, config_root, args.config_name, args.override, warnings)
    else:
        if warnings:
            for warning in warnings:
                print(f"warning: {warning}", file=sys.stderr)
        dump_config(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

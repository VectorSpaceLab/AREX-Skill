#!/usr/bin/env python3
"""Read-only NAVSIM training-config preflight.

This helper validates a YAML config and/or a small set of Hydra-style dotted
``KEY=VALUE`` overrides. It does not import NAVSIM, resolve Hydra defaults,
construct a SceneLoader, touch a cache, create directories, download data, or
launch training. It is intentionally conservative: split legality and the
cache-only flag assertion are checked before any resource recommendation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by environment diagnosis
    raise SystemExit("PyYAML is required for config-file inspection; no training was started") from exc


TRAINING_SPLITS = {"navtrain", "trainval", "mini", "navmini"}
FORBIDDEN_TRAINING_SPLITS = {
    "test",
    "navtest",
    "navtest_two_stage",
    "navhard_two_stage",
    "navsafe_two_stage",
    "warmup_two_stage",
    "warmup_navsafe_two_stage_extended",
    "private_test_two_stage",
    "private_test_hard_two_stage",
}


def parse_scalar(raw: str) -> Any:
    """Parse a Hydra-like scalar/list value without evaluating code."""
    value = yaml.safe_load(raw)
    return raw if value is None and raw.lower() not in {"null", "~"} else value


def set_dotted(config: MutableMapping[str, Any], dotted_key: str, value: Any) -> None:
    """Set a dotted key in a nested mapping for safe override inspection."""
    parts = dotted_key.split(".")
    current: MutableMapping[str, Any] = config
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, MutableMapping):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def get_dotted(config: Mapping[str, Any], dotted_key: str, default: Any = None) -> Any:
    """Read a dotted key from a mapping."""
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    """Load a mapping with PyYAML's safe loader, or return an empty config."""
    if path is None:
        return {}
    if not path.is_file():
        raise ValueError(f"config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, Mapping):
        raise ValueError("config root must be a YAML mapping")
    return dict(loaded)


def infer_split(config: Mapping[str, Any], explicit: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Return a split name and a note when only the underlying data split is known."""
    if explicit:
        return explicit, None
    selected = config.get("train_test_split")
    if isinstance(selected, str):
        return selected, None
    if isinstance(selected, Mapping):
        for key in ("name", "config_name", "split"):
            if isinstance(selected.get(key), str):
                return selected[key], None
        data_split = selected.get("data_split")
        if isinstance(data_split, str):
            return data_split, f"only data_split={data_split!r} was found; pass --split to distinguish filtered configs"
    selected = config.get("split")
    if isinstance(selected, str):
        return selected, "split is a legacy/top-level field; the runner selects the group with train_test_split"
    return None, "no split was supplied; pass --split or include train_test_split in the inspected config"


def bool_value(config: Mapping[str, Any], key: str, default: bool) -> bool:
    """Read a boolean while preserving a useful error for malformed values."""
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(f"{key} must be boolean, got {value!r}")


def inspect(config: Mapping[str, Any], split: Optional[str], purpose: str, agent: Optional[str]) -> Dict[str, Any]:
    """Build a JSON-serializable preflight report."""
    errors: List[str] = []
    warnings: List[str] = []
    selected_split, split_note = infer_split(config, split)
    if split_note:
        warnings.append(split_note)

    if purpose == "training":
        if selected_split in FORBIDDEN_TRAINING_SPLITS:
            errors.append(f"split {selected_split!r} is not legal for training")
        elif selected_split is None:
            errors.append("training split is unresolved")
        elif selected_split not in TRAINING_SPLITS:
            warnings.append(
                f"split {selected_split!r} is not in the known training set; require explicit policy approval for a custom split"
            )

    try:
        use_cache_without_dataset = bool_value(config, "use_cache_without_dataset", False)
        force_cache_computation = bool_value(config, "force_cache_computation", True)
    except ValueError as exc:
        errors.append(str(exc))
        use_cache_without_dataset = False
        force_cache_computation = False

    cache_path = config.get("cache_path")
    if use_cache_without_dataset and force_cache_computation:
        errors.append(
            "use_cache_without_dataset=true requires force_cache_computation=false; the training runner asserts this"
        )
    if use_cache_without_dataset and cache_path is None:
        errors.append("use_cache_without_dataset=true requires a non-null cache_path")
    if use_cache_without_dataset and isinstance(cache_path, str) and not cache_path.strip():
        errors.append("use_cache_without_dataset=true requires a non-empty cache_path")

    trainer = get_dotted(config, "trainer.params", {})
    if not isinstance(trainer, Mapping):
        errors.append("trainer.params must be a mapping")
        trainer = {}
    dataloader = get_dotted(config, "dataloader.params", {})
    if not isinstance(dataloader, Mapping):
        errors.append("dataloader.params must be a mapping")
        dataloader = {}

    num_workers = dataloader.get("num_workers")
    if num_workers == 0 and dataloader.get("prefetch_factor") not in (None, "null"):
        warnings.append("num_workers=0 normally requires prefetch_factor=null or omission")

    accelerator = trainer.get("accelerator", "unspecified")
    strategy = trainer.get("strategy", "unspecified")
    precision = trainer.get("precision", "unspecified")
    if accelerator == "gpu" and strategy == "ddp" and trainer.get("devices") in (None, 1, "1"):
        warnings.append("single-device GPU plans should review strategy=ddp; strategy=auto and devices=1 are safer")
    if accelerator == "cpu" and precision == "16-mixed":
        warnings.append("16-mixed is a GPU-oriented plan; use precision=32-true for a CPU smoke")

    return {
        "status": "error" if errors else "ok",
        "purpose": purpose,
        "split": selected_split,
        "agent": agent or config.get("agent", "unspecified"),
        "cache": {
            "path": cache_path,
            "use_cache_without_dataset": use_cache_without_dataset,
            "force_cache_computation": force_cache_computation,
        },
        "resources": {
            "accelerator": accelerator,
            "strategy": strategy,
            "devices": trainer.get("devices", "unspecified"),
            "precision": precision,
            "batch_size": dataloader.get("batch_size", "unspecified"),
            "num_workers": num_workers if num_workers is not None else "unspecified",
        },
        "errors": errors,
        "warnings": warnings,
        "side_effects": "none: YAML parsing and validation only",
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="optional YAML mapping to inspect")
    parser.add_argument("--split", help="selected train_test_split group, e.g. navtrain")
    parser.add_argument("--purpose", choices=("training", "planning"), default="training")
    parser.add_argument("--agent", help="agent config name to report")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="safe dotted override to inspect; may be repeated, e.g. use_cache_without_dataset=true",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the no-side-effect preflight and return a shell status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        for override in args.override:
            if "=" not in override:
                raise ValueError(f"override must use KEY=VALUE: {override!r}")
            key, raw_value = override.split("=", 1)
            if not key or key.startswith("_"):
                raise ValueError(f"unsupported override key: {key!r}")
            set_dotted(config, key, parse_scalar(raw_value))
        report = inspect(config, args.split, args.purpose, args.agent)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report = {"status": "error", "errors": [str(exc)], "warnings": [], "side_effects": "none"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for key in ("purpose", "split", "agent"):
            if key in report:
                print(f"{key}: {report[key]}")
        for message in report.get("errors", []):
            print(f"ERROR: {message}", file=sys.stderr)
        for message in report.get("warnings", []):
            print(f"WARNING: {message}")
        resources = report.get("resources")
        if resources:
            print("resources: " + ", ".join(f"{key}={value}" for key, value in resources.items()))
        cache = report.get("cache")
        if cache:
            print("cache: " + ", ".join(f"{key}={value}" for key, value in cache.items()))

    return 1 if report.get("status") == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())

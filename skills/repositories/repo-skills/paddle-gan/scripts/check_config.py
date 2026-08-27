#!/usr/bin/env python3
"""Safely inspect a PaddleGAN YAML configuration without running PaddleGAN."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Tuple


class ConfigError(Exception):
    """An actionable configuration or override error."""


def import_yaml() -> Any:
    """Import PyYAML lazily so that ``--help`` works even when it is missing."""
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError(
            "PyYAML is required to inspect a config; install the 'PyYAML' package and try again"
        ) from exc
    return yaml


def _format_path(parts: Sequence[str]) -> str:
    return ".".join(parts) if parts else "<root>"


def _validate_mapping_keys(value: Any, parts: Tuple[str, ...] = ()) -> None:
    """Require string mapping keys, as expected by PaddleGAN dotted paths."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ConfigError(
                    "mapping at {} has a non-string key {!r}; PaddleGAN config keys must be strings".format(
                        _format_path(parts), key
                    )
                )
            _validate_mapping_keys(child, parts + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_mapping_keys(child, parts + (str(index),))


def read_config(config_path: str, yaml_module: Any) -> Tuple[Dict[str, Any], Path]:
    """Read one local YAML file with PyYAML's non-executing safe loader."""
    path = Path(config_path).expanduser()
    if not path.exists():
        raise ConfigError("config file does not exist: {}".format(path))
    if not path.is_file():
        raise ConfigError("config path is not a regular file: {}".format(path))

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError("config is not valid UTF-8: {} ({})".format(path, exc)) from exc
    except OSError as exc:
        raise ConfigError("could not read config {}: {}".format(path, exc)) from exc

    try:
        loaded = yaml_module.safe_load(text)
    except yaml_module.YAMLError as exc:
        problem = getattr(exc, "problem", None)
        mark = getattr(exc, "problem_mark", None)
        detail = str(problem or exc).strip()
        if mark is not None:
            detail = "{} at line {}, column {}".format(detail, mark.line + 1, mark.column + 1)
        raise ConfigError("invalid YAML in {}: {}".format(path, detail)) from exc

    if loaded is None:
        raise ConfigError("config is empty: {}".format(path))
    if not isinstance(loaded, dict):
        raise ConfigError(
            "config root must be a mapping, not {}: {}".format(type(loaded).__name__, path)
        )
    _validate_mapping_keys(loaded)
    return loaded, path.resolve()


def parse_override(assignment: str, yaml_module: Any) -> Tuple[List[str], Any]:
    """Parse ``dotted.path=YAML-value`` without evaluating Python code."""
    if "=" not in assignment:
        raise ConfigError(
            "malformed override {!r}: expected dotted.key=value".format(assignment)
        )
    raw_path, raw_value = assignment.split("=", 1)
    if not raw_path:
        raise ConfigError("malformed override {!r}: key path is empty".format(assignment))
    if raw_path != raw_path.strip():
        raise ConfigError(
            "malformed override {!r}: key path must not start or end with whitespace".format(
                assignment
            )
        )

    parts = raw_path.split(".")
    if any(not part for part in parts):
        raise ConfigError(
            "malformed override {!r}: dotted path contains an empty component".format(
                assignment
            )
        )
    if any(part != part.strip() for part in parts):
        raise ConfigError(
            "malformed override {!r}: path components must not contain surrounding whitespace".format(
                assignment
            )
        )

    try:
        value = yaml_module.safe_load(raw_value)
    except yaml_module.YAMLError as exc:
        problem = getattr(exc, "problem", None)
        raise ConfigError(
            "invalid YAML value in override {!r}: {}".format(
                assignment, str(problem or exc).strip()
            )
        ) from exc
    return parts, value


def apply_override(config: Dict[str, Any], assignment: str, yaml_module: Any) -> Dict[str, Any]:
    """Apply one override, refusing to create misspelled or missing paths."""
    parts, value = parse_override(assignment, yaml_module)
    current: Any = config

    for position, part in enumerate(parts):
        final = position == len(parts) - 1
        parent_path = _format_path(parts[:position])

        if isinstance(current, MutableMapping):
            if part not in current:
                raise ConfigError(
                    "override path {!r} does not exist: missing key {!r} beneath {}".format(
                        _format_path(parts), part, parent_path
                    )
                )
            if final:
                current[part] = value
                break
            current = current[part]
            continue

        if isinstance(current, MutableSequence) and not isinstance(current, (str, bytes, bytearray)):
            if not re.match(r"^(0|[1-9][0-9]*)$", part):
                raise ConfigError(
                    "override path {!r} requires a non-negative list index at {!r}".format(
                        _format_path(parts), part
                    )
                )
            index = int(part)
            if index >= len(current):
                raise ConfigError(
                    "override path {!r} has list index {} out of range at {} (length {})".format(
                        _format_path(parts), index, parent_path, len(current)
                    )
                )
            if final:
                current[index] = value
                break
            current = current[index]
            continue

        raise ConfigError(
            "override path {!r} cannot descend through {} at {}".format(
                _format_path(parts), type(current).__name__, parent_path
            )
        )

    return {"assignment": assignment, "path": _format_path(parts), "value": value}


def load_config(
    config_path: str, overrides: Sequence[str]
) -> Tuple[Dict[str, Any], Path, List[Dict[str, Any]], Any]:
    """Load a config and apply validated overrides in command-line order."""
    yaml_module = import_yaml()
    config, resolved_path = read_config(config_path, yaml_module)
    applied = [apply_override(config, assignment, yaml_module) for assignment in overrides]
    return config, resolved_path, applied, yaml_module


def _mapping_name(value: Any) -> Optional[Any]:
    return value.get("name") if isinstance(value, Mapping) else None


def build_summary(
    config: Dict[str, Any], resolved_path: Path, applied: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    """Extract common PaddleGAN fields without assuming one model family."""
    model = config.get("model")
    dataset = config.get("dataset")
    scheduler = config.get("lr_scheduler")
    optimizer = config.get("optimizer")

    dataset_splits: List[Dict[str, Any]] = []
    if isinstance(dataset, Mapping):
        for split, settings in dataset.items():
            dataset_splits.append({"split": split, "name": _mapping_name(settings)})

    return {
        "config_file": str(resolved_path),
        "top_level_keys": sorted(config.keys()),
        "model_name": _mapping_name(model),
        "total_iters": config.get("total_iters"),
        "epochs": config.get("epochs"),
        "output_dir": config.get("output_dir"),
        "dataset_splits": dataset_splits,
        "lr_scheduler_name": _mapping_name(scheduler),
        "optimizers": sorted(optimizer.keys()) if isinstance(optimizer, Mapping) else [],
        "export_model_entries": (
            len(config["export_model"]) if isinstance(config.get("export_model"), list) else None
        ),
        "override_count": len(applied),
    }


def _json_default(value: Any) -> Any:
    """Represent uncommon SafeLoader values such as dates and sets."""
    if isinstance(value, set):
        return sorted(value, key=repr)
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)


def print_human(summary: Dict[str, Any], applied: Sequence[Dict[str, Any]]) -> None:
    print("PaddleGAN configuration summary")
    print("Config: {}".format(summary["config_file"]))
    print("Top-level keys: {}".format(", ".join(summary["top_level_keys"])))
    if summary["model_name"] is not None:
        print("Model: {}".format(summary["model_name"]))
    if summary["total_iters"] is not None:
        print("Total iterations: {}".format(summary["total_iters"]))
    if summary["epochs"] is not None:
        print("Epochs: {}".format(summary["epochs"]))
    if summary["output_dir"] is not None:
        print("Output directory: {}".format(summary["output_dir"]))
    if summary["dataset_splits"]:
        split_text = []
        for item in summary["dataset_splits"]:
            split_text.append(
                "{} ({})".format(item["split"], item["name"])
                if item["name"] is not None
                else str(item["split"])
            )
        print("Dataset splits: {}".format(", ".join(split_text)))
    if summary["lr_scheduler_name"] is not None:
        print("LR scheduler: {}".format(summary["lr_scheduler_name"]))
    if summary["optimizers"]:
        print("Optimizers: {}".format(", ".join(summary["optimizers"])))
    if summary["export_model_entries"] is not None:
        print("Export entries: {}".format(summary["export_model_entries"]))
    if applied:
        print("Applied overrides:")
        for item in applied:
            print("  {} = {!r}".format(item["path"], item["value"]))
    print("Validation only: no PaddleGAN modules were imported and no training was started.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely load and summarize a PaddleGAN YAML config. Dotted overrides "
            "must target existing keys; this command never starts training."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        metavar="CONFIG",
        help="config file (alternative to -c/--config)",
    )
    parser.add_argument(
        "-c",
        "--config",
        "--config-file",
        dest="config_option",
        metavar="CONFIG",
        help="PaddleGAN YAML config file",
    )
    parser.add_argument(
        "-o",
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override an existing dotted path using a YAML-parsed value (repeatable)",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="emit summary and resolved config as JSON")
    output.add_argument(
        "--show-config",
        action="store_true",
        help="emit the resolved config as safe YAML instead of a summary",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.config_path and args.config_option:
        parser.error("specify the config either positionally or with -c/--config, not both")
    config_path = args.config_option or args.config_path
    if not config_path:
        parser.error("a config file is required (pass CONFIG or -c CONFIG)")

    try:
        config, resolved_path, applied, yaml_module = load_config(config_path, args.override)
    except ConfigError as exc:
        parser.error(str(exc))

    summary = build_summary(config, resolved_path, applied)
    if args.json:
        payload = {
            "summary": summary,
            "applied_overrides": applied,
            "resolved_config": config,
            "safety": {"training_started": False, "paddlegan_imported": False},
        }
        print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    elif args.show_config:
        try:
            rendered = yaml_module.safe_dump(config, sort_keys=False, allow_unicode=True)
        except TypeError:  # pragma: no cover - compatibility with older PyYAML
            rendered = yaml_module.safe_dump(config, allow_unicode=True)
        sys.stdout.write(rendered)
        if rendered and not rendered.endswith("\n"):
            sys.stdout.write("\n")
    else:
        print_human(summary, applied)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

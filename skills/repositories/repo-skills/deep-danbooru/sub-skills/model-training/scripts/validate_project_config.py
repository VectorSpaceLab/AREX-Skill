#!/usr/bin/env python3
"""Read-only validation for a DeepDanbooru 1.0.0 project configuration."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

SUPPORTED_MODELS = {
    "resnet_152",
    "resnet_custom_v1",
    "resnet_custom_v2",
    "resnet_custom_v3",
    "resnet_custom_v4",
}
SUPPORTED_OPTIMIZERS = {"adam", "sgd", "rmsprop"}
SUPPORTED_LOSSES = {"binary_crossentropy", "focal_loss"}

REQUIRED_FIELDS = {
    "image_width",
    "image_height",
    "database_path",
    "minimum_tag_count",
    "model",
    "optimizer",
    "minibatch_size",
    "epoch_count",
    "checkpoint_frequency_mb",
    "console_logging_frequency_mb",
    "rotation_range",
    "scale_range",
    "shift_range",
}
OPTIONAL_DEFAULTS = {
    "learning_rate": 0.001,
    "export_model_per_epoch": 10,
    "mixed_precision": False,
    "loss": "binary_crossentropy",
}
KNOWN_FIELDS = REQUIRED_FIELDS | set(OPTIONAL_DEFAULTS) | {"learning_rates"}


class DuplicateKeyError(ValueError):
    """Raised when JSON contains an ambiguous duplicate object key."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream, object_pairs_hook=_object_without_duplicates)
    if not isinstance(value, dict):
        raise ValueError("project JSON root must be an object")
    return value


def resolve_target(target: Path) -> tuple[Path, Path]:
    expanded = target.expanduser()
    if expanded.is_dir():
        project_dir = expanded.resolve()
        config_path = project_dir / "project.json"
    else:
        config_path = expanded.resolve()
        project_dir = config_path.parent
    return config_path, project_dir


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_int(
    config: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    minimum: int | None = None,
) -> None:
    value = config.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{field} must be an integer")
    elif minimum is not None and value < minimum:
        errors.append(f"{field} must be >= {minimum}, got {value}")


def _check_range(
    config: dict[str, Any],
    field: str,
    errors: list[str],
    warnings: list[str],
    *,
    positive: bool = False,
) -> None:
    value = config.get(field)
    if value is None or value == []:
        warnings.append(f"{field} is disabled")
        return
    if not isinstance(value, list) or len(value) != 2:
        errors.append(f"{field} must be null, empty, or a two-number JSON array")
        return
    if not all(_is_number(item) for item in value):
        errors.append(f"{field} endpoints must be finite numbers")
        return
    lower, upper = value
    if lower > upper:
        errors.append(f"{field} lower endpoint must not exceed upper endpoint")
    if positive and (lower <= 0 or upper <= 0):
        errors.append(f"{field} endpoints must be positive")


def validate_config(
    config: dict[str, Any], project_dir: Path, runtime_cwd: Path
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    info: dict[str, Any] = {}

    for field in sorted(REQUIRED_FIELDS - set(config)):
        errors.append(f"missing required field: {field}")
    for field, default in OPTIONAL_DEFAULTS.items():
        if field not in config:
            warnings.append(f"{field} is absent; training fallback is {default!r}")
    unknown = sorted(set(config) - KNOWN_FIELDS)
    if unknown:
        warnings.append("unknown fields are ignored by training: " + ", ".join(unknown))

    if "image_width" in config:
        _check_int(config, "image_width", errors, minimum=1)
    if "image_height" in config:
        _check_int(config, "image_height", errors, minimum=1)
    if "minimum_tag_count" in config:
        _check_int(config, "minimum_tag_count", errors, minimum=0)
    if "minibatch_size" in config:
        _check_int(config, "minibatch_size", errors, minimum=1)
    if "epoch_count" in config:
        _check_int(config, "epoch_count", errors, minimum=1)
    if "checkpoint_frequency_mb" in config:
        _check_int(config, "checkpoint_frequency_mb", errors, minimum=1)
    if "console_logging_frequency_mb" in config:
        _check_int(config, "console_logging_frequency_mb", errors, minimum=1)

    export_interval = config.get("export_model_per_epoch", OPTIONAL_DEFAULTS["export_model_per_epoch"])
    if not isinstance(export_interval, int) or isinstance(export_interval, bool):
        errors.append("export_model_per_epoch must be an integer")
    elif export_interval < 0:
        errors.append("export_model_per_epoch must be >= 0")

    model = config.get("model")
    if model not in SUPPORTED_MODELS:
        errors.append(
            "model must be one of: " + ", ".join(sorted(SUPPORTED_MODELS))
        )
    optimizer = config.get("optimizer")
    if optimizer not in SUPPORTED_OPTIMIZERS:
        errors.append(
            "optimizer must be one of: " + ", ".join(sorted(SUPPORTED_OPTIMIZERS))
        )
    loss = config.get("loss", OPTIONAL_DEFAULTS["loss"])
    if loss not in SUPPORTED_LOSSES:
        errors.append("loss must be one of: " + ", ".join(sorted(SUPPORTED_LOSSES)))

    learning_rate = config.get("learning_rate", OPTIONAL_DEFAULTS["learning_rate"])
    if not _is_number(learning_rate) or learning_rate <= 0:
        errors.append("learning_rate must be a positive finite number")

    schedule = config.get("learning_rates")
    if schedule is not None:
        if not isinstance(schedule, list):
            errors.append("learning_rates must be null or a JSON array")
        else:
            epochs: list[int] = []
            for index, entry in enumerate(schedule):
                prefix = f"learning_rates[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                if set(entry) != {"used_epoch", "learning_rate"}:
                    errors.append(
                        f"{prefix} must contain exactly used_epoch and learning_rate"
                    )
                    continue
                used_epoch = entry["used_epoch"]
                rate = entry["learning_rate"]
                if not isinstance(used_epoch, int) or isinstance(used_epoch, bool) or used_epoch < 0:
                    errors.append(f"{prefix}.used_epoch must be a non-negative integer")
                else:
                    epochs.append(used_epoch)
                if not _is_number(rate) or rate <= 0:
                    errors.append(f"{prefix}.learning_rate must be positive and finite")
            if epochs != sorted(epochs):
                warnings.append("learning_rates entries are not sorted by used_epoch")
            if len(epochs) != len(set(epochs)):
                warnings.append("learning_rates contains duplicate used_epoch thresholds")

    mixed = config.get("mixed_precision", OPTIONAL_DEFAULTS["mixed_precision"])
    if not isinstance(mixed, bool):
        errors.append("mixed_precision must be a JSON boolean")

    for field in ("rotation_range", "shift_range"):
        if field in config:
            _check_range(config, field, errors, warnings)
    if "scale_range" in config:
        _check_range(config, "scale_range", errors, warnings, positive=True)

    database_value = config.get("database_path")
    if database_value is None:
        errors.append("database_path is null; set it before training")
    elif not isinstance(database_value, str) or not database_value.strip():
        errors.append("database_path must be a non-empty path string")
    else:
        raw_database = Path(database_value).expanduser()
        resolved_database = (
            raw_database.resolve()
            if raw_database.is_absolute()
            else (runtime_cwd / raw_database).resolve()
        )
        info["database_path"] = str(resolved_database)
        info["database_path_is_absolute"] = raw_database.is_absolute()
        if not raw_database.is_absolute():
            warnings.append(
                "database_path is relative and training resolves it from the process working directory"
            )

    info["project_dir"] = str(project_dir)
    info["tags_path"] = str(project_dir / "tags.txt")
    info["model"] = model
    info["optimizer"] = optimizer
    info["loss"] = loss
    if isinstance(config.get("image_height"), int) and isinstance(config.get("image_width"), int):
        info["input_shape"] = [config["image_height"], config["image_width"], 3]

    return {"errors": errors, "warnings": warnings, "info": info}


def _print_human(report: dict[str, Any], warnings_as_errors: bool) -> None:
    failed = bool(report["errors"] or (warnings_as_errors and report["warnings"]))
    print(f"{'FAIL' if failed else 'PASS'}: {report['config_path']}")
    for message in report["errors"]:
        print(f"  error: {message}")
    for message in report["warnings"]:
        print(f"  warning: {message}")
    for key, value in sorted(report.get("info", {}).items()):
        print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DeepDanbooru 1.0.0 project.json values without importing "
            "DeepDanbooru or launching training."
        )
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Project directory or project.json file.",
    )
    parser.add_argument(
        "--runtime-cwd",
        type=Path,
        default=Path.cwd(),
        help="Working directory used to resolve a relative database_path (default: current directory).",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Also require the resolved database file and project tags.txt to exist.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return failure when warnings are present.",
    )
    args = parser.parse_args(argv)

    config_path, project_dir = resolve_target(args.target)
    runtime_cwd = args.runtime_cwd.expanduser().resolve()
    report: dict[str, Any] = {
        "config_path": str(config_path),
        "runtime_cwd": str(runtime_cwd),
        "errors": [],
        "warnings": [],
        "info": {},
    }
    try:
        if not config_path.is_file():
            raise FileNotFoundError(f"project config does not exist: {config_path}")
        config = load_config(config_path)
        validated = validate_config(config, project_dir, runtime_cwd)
        report.update(validated)
        if args.check_paths:
            database_text = report["info"].get("database_path")
            if database_text and not Path(database_text).is_file():
                report["errors"].append(f"database file does not exist: {database_text}")
            tags_path = project_dir / "tags.txt"
            if not tags_path.is_file():
                report["errors"].append(f"tags file does not exist: {tags_path}")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report["errors"].append(str(exc))

    failed = bool(report["errors"] or (args.warnings_as_errors and report["warnings"]))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report, args.warnings_as_errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

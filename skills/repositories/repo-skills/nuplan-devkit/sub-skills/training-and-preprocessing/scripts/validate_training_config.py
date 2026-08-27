#!/usr/bin/env python3
"""Safely inspect a nuPlan training YAML document.

The validator deliberately imports no nuPlan, Hydra, Torch, Lightning, or
model code. It uses ``yaml.safe_load`` only, so it can report structural issues
before a constructor, dataset, cache, weight download, or trainer is touched.
It is read-only and deterministic: messages are emitted in fixed order and no
configuration values are resolved or mutated.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - depends on caller environment
    yaml = None  # type: ignore
    _YAML_IMPORT_ERROR = exc
else:
    _YAML_IMPORT_ERROR = None


# These are the four standalone sections required by this operating route.
# A Hydra source fragment can use ``defaults`` instead; validate its materialized
# composition before execution if the fragment does not contain these sections.
REQUIRED_TOP_LEVEL_FIELDS: Tuple[str, ...] = ("training", "model", "cache", "worker")
KNOWN_PY_FUNCS = ("cache", "test", "train")
KNOWN_AGGREGATIONS = ("max", "mean", "sum")
KNOWN_MODEL_TARGETS = (
    "nuplan.planning.training.modeling.models.raster_model.RasterModel",
    "nuplan.planning.training.modeling.models.lanegcn_model.LaneGCN",
    "nuplan.planning.training.modeling.models.simple_vector_map_model.VectorMapSimpleMLP",
    "nuplan.planning.training.modeling.models.urban_driver_open_loop_model.UrbanDriverOpenLoopModel",
)


def _is_mapping(value: Any) -> bool:
    """Return whether ``value`` is a YAML mapping."""

    return isinstance(value, Mapping)


def _walk_mappings(value: Any, seen: Optional[set[int]] = None) -> Iterable[Mapping[str, Any]]:
    """Yield nested mappings without looping on YAML aliases/recursive values."""

    if seen is None:
        seen = set()
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        yield value
        for child in value.values():
            yield from _walk_mappings(child, seen)
    elif isinstance(value, list):
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        for child in value:
            yield from _walk_mappings(child, seen)


def _walk_targets(value: Any) -> List[str]:
    """Collect textual Hydra target values without importing them."""

    targets: List[str] = []
    for mapping in _walk_mappings(value):
        if "_target_" in mapping:
            targets.append(str(mapping["_target_"]))
    return targets


def _lookup(data: Mapping[str, Any], dotted_path: str) -> Tuple[bool, Any]:
    """Read a dotted path and preserve the distinction between missing/null."""

    current: Any = data
    for part in dotted_path.split("."):
        if not _is_mapping(current) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _looks_unresolved(value: Any) -> bool:
    """Identify unresolved Hydra/OmegaConf-looking scalar strings only."""

    return isinstance(value, str) and ("???" in value or "${" in value)


def _unresolved_values(value: Any, seen: Optional[set[int]] = None) -> List[str]:
    """Return deterministic ``path=value``-like diagnostics for unresolved values."""

    # The path is intentionally omitted: the standalone parser has no need to
    # reconstruct a potentially ambiguous path through YAML aliases.
    if seen is None:
        seen = set()
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in seen:
            return []
        seen.add(marker)
        found: List[str] = []
        for key in sorted(value, key=lambda item: str(item)):
            child = value[key]
            if _looks_unresolved(child):
                found.append(f"{key}={child}")
            else:
                found.extend(_unresolved_values(child, seen))
        return found
    if isinstance(value, list):
        marker = id(value)
        if marker in seen:
            return []
        seen.add(marker)
        found = []
        for child in value:
            found.extend(_unresolved_values(child, seen))
        return found
    return []


def _check_mapping_field(errors: List[str], data: Mapping[str, Any], field: str) -> None:
    """Require a present top-level section to be a mapping."""

    value = data.get(field)
    if not _is_mapping(value):
        errors.append(f"{field}: expected a mapping, got {type(value).__name__}")


def _check_optional_types(errors: List[str], data: Mapping[str, Any]) -> None:
    """Check inexpensive scalar/collection invariants without resolving config."""

    present, py_func = _lookup(data, "py_func")
    if present and not _looks_unresolved(py_func) and py_func not in KNOWN_PY_FUNCS:
        errors.append(f"py_func must be one of {list(KNOWN_PY_FUNCS)}, got {py_func!r}")

    present, aggregate = _lookup(data, "objective_aggregate_mode")
    if present and not _looks_unresolved(aggregate) and aggregate not in KNOWN_AGGREGATIONS:
        errors.append(
            "objective_aggregate_mode must be one of "
            f"{list(KNOWN_AGGREGATIONS)}, got {aggregate!r}"
        )

    present, cache_path = _lookup(data, "cache.cache_path")
    _, use_cache = _lookup(data, "cache.use_cache_without_dataset")
    _, force_compute = _lookup(data, "cache.force_feature_computation")
    if use_cache is True and (not present or cache_path is None or cache_path == ""):
        errors.append("cache.use_cache_without_dataset=true requires cache.cache_path")
    if use_cache is True and force_compute is True:
        errors.append(
            "cache.use_cache_without_dataset and cache.force_feature_computation "
            "cannot both be true: a CachedScenario cannot recompute missing data"
        )

    for dotted_path in (
        "cache.use_cache_without_dataset",
        "cache.force_feature_computation",
        "cache.cleanup_cache",
    ):
        present, value = _lookup(data, dotted_path)
        if present and value is not None and not isinstance(value, bool):
            errors.append(f"{dotted_path}: expected bool, got {type(value).__name__}")

    present, batch_size = _lookup(data, "data_loader.params.batch_size")
    if present and isinstance(batch_size, int) and not isinstance(batch_size, bool) and batch_size <= 0:
        errors.append("data_loader.params.batch_size must be > 0")
    present, num_workers = _lookup(data, "data_loader.params.num_workers")
    if present and isinstance(num_workers, int) and not isinstance(num_workers, bool) and num_workers < 0:
        errors.append("data_loader.params.num_workers must be >= 0")

    present, precision = _lookup(data, "lightning.trainer.params.precision")
    if present and precision not in (16, 32, "16", "32") and not _looks_unresolved(precision):
        errors.append("lightning.trainer.params.precision should be 16 or 32")


def _check_model_shape_contract(errors: List[str], warnings: List[str], model: Any) -> List[str]:
    """Check only visible YAML shape/type hints; never instantiate a model."""

    if not _is_mapping(model):
        return []

    targets = _walk_targets(model)
    feature_builders = model.get("feature_builders")
    target_builders = model.get("target_builders")
    if feature_builders is not None and not isinstance(feature_builders, list):
        errors.append("model.feature_builders must be a list when supplied")
    if target_builders is not None and not isinstance(target_builders, list):
        errors.append("model.target_builders must be a list when supplied")
    if isinstance(feature_builders, list) and not feature_builders:
        errors.append("model.feature_builders must not be empty")

    if "_target_" not in model:
        warnings.append("model has no top-level _target_; it may be a Hydra composition fragment")
    elif str(model["_target_"]) not in KNOWN_MODEL_TARGETS and not _looks_unresolved(model["_target_"]):
        warnings.append(
            "model._target_ is not one of the four bundled planning model targets; "
            "custom model construction is outside this static check"
        )

    if isinstance(target_builders, list):
        target_names = [
            str(item["_target_"])
            for item in target_builders
            if _is_mapping(item) and "_target_" in item
        ]
        if target_names and not any("EgoTrajectoryTargetBuilder" in name for name in target_names):
            warnings.append(
                "no EgoTrajectoryTargetBuilder target is visible; trajectory objective compatibility needs review"
            )
    return targets


def inspect_config(path: Path) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Parse one YAML file and return ``errors, warnings, summary``."""

    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {"path": str(path), "keys": [], "targets": []}

    if not path.exists():
        return [f"file does not exist: {path}"], warnings, summary
    if not path.is_file():
        return [f"not a regular file: {path}"], warnings, summary
    if yaml is None:
        return [f"PyYAML is unavailable: {_YAML_IMPORT_ERROR}"], warnings, summary

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (OSError, UnicodeError) as exc:
        return [f"cannot read YAML: {exc}"], warnings, summary
    except yaml.YAMLError as exc:  # type: ignore[union-attr]
        return [f"cannot parse YAML: {exc}"], warnings, summary

    if not _is_mapping(data):
        return ["top-level YAML value must be a mapping"], warnings, summary

    summary["keys"] = sorted(str(key) for key in data.keys())
    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in data]
    if missing:
        errors.append("missing required top-level field(s): " + ", ".join(missing))

    # The model, cache, and worker sections are mappings in the materialized
    # config. ``training`` may be a mapping or a string group marker, but null
    # is not a useful standalone section.
    for field in ("model", "cache", "worker"):
        if field in data:
            _check_mapping_field(errors, data, field)
    if "training" in data and data["training"] is None:
        errors.append("training: expected a mapping or a Hydra group name, got null")

    _check_optional_types(errors, data)
    summary["targets"] = _check_model_shape_contract(errors, warnings, data.get("model"))

    unresolved = _unresolved_values(data)
    if unresolved:
        summary["unresolved_hydra_values"] = True
        warnings.append(
            "unresolved Hydra-looking values remain; resolve them before execution: "
            + ", ".join(unresolved[:8])
        )
    else:
        summary["unresolved_hydra_values"] = False
    return errors, warnings, summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Parse nuPlan training YAML safely. No Hydra composition, model "
            "instantiation, dataset/cache access, network access, or training is performed."
        )
    )
    parser.add_argument(
        "--config",
        nargs="+",
        required=True,
        metavar="FILE",
        help="one or more YAML files to read (read-only)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return nonzero when warnings, including unresolved values, are present",
    )
    parser.add_argument(
        "--show-targets",
        action="store_true",
        help="print discovered Hydra _target_ strings without importing them",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    failed = False
    for raw_path in args.config:
        path = Path(raw_path).expanduser()
        errors, warnings, summary = inspect_config(path)
        print(f"[{path}]")
        for message in errors:
            print(f"ERROR: {message}")
        for message in warnings:
            print(f"WARNING: {message}")
        if args.show_targets:
            targets = summary.get("targets", [])
            print("TARGETS: " + (", ".join(targets) if targets else "(none)"))
        strict_failure = args.strict and bool(warnings)
        if strict_failure:
            failed = True
            print("ERROR: --strict promotes warnings to failures")
        if errors:
            failed = True
        elif not strict_failure:
            print("OK: YAML parsed and structural checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

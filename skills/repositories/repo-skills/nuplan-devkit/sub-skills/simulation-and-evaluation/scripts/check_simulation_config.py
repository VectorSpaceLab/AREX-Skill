#!/usr/bin/env python3
"""Validate local nuPlan config names and Hydra override syntax without running anything.

This checker intentionally does not import Hydra or nuPlan. It performs only
filesystem existence checks and shallow text checks, so it never composes a
config, imports a configured target, creates an output directory, reads a
private environment, starts simulation/metrics/aggregation/nuBoard, or uses a
network. A successful result is a naming/syntax preflight, not proof that a
runtime is installable or that data are available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

# This is deliberately narrower than Hydra's complete grammar. It catches
# common typos while leaving values opaque and never evaluating them.
_OVERRIDE_KEY = re.compile(
    r"^\+{0,2}[A-Za-z_][A-Za-z0-9_.\-/]*(?:\[[^\]\r\n]+\])?$"
)
_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_YAML_SUFFIXES = {".yaml", ".yml"}

MODE_ALIASES = {
    "simulation": "simulation",
    "metric": "metrics",
    "metrics": "metrics",
    "aggregate": "aggregate",
    "aggregator": "aggregate",
    "metric-aggregator": "aggregate",
    "nuboard": "nuboard",
}

# These are the entry-point config names in this package. A caller can replace
# them with --config/--config-name when using a custom config file.
DEFAULT_CONFIG_NAMES = {
    "simulation": "default_simulation",
    "metrics": "default_simulation",
    "aggregate": "default_run_metric_aggregator",
    "nuboard": "default_nuboard",
}


def _canonical_mode(mode: str) -> Optional[str]:
    """Return the canonical mode, or None for an unsupported mode."""
    return MODE_ALIASES.get(mode)


def _parse_override(raw: str) -> Tuple[str, str]:
    """Validate one opaque ``key=value`` override and return its two parts."""
    if "\x00" in raw or "\n" in raw or "\r" in raw:
        raise ValueError("override contains a control character")
    if "=" not in raw:
        raise ValueError("override must have the form key=value")

    key, value = raw.split("=", 1)
    if not _OVERRIDE_KEY.fullmatch(key):
        raise ValueError(f"invalid override key: {key!r}")
    if value == "":
        raise ValueError(f"override {key!r} has an empty value")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"override {key!r} contains a control character")
    return key, value


def _config_candidates(config_root: Path, name: str) -> List[Path]:
    """Return deterministic candidates for a config name or filename."""
    path = Path(name)
    if path.is_absolute():
        return [path]

    candidates = [config_root / path]
    if path.suffix not in _YAML_SUFFIXES:
        candidates.extend([config_root / f"{name}.yaml", config_root / f"{name}.yml"])
    # Preserve order while removing duplicates (for example, a supplied .yaml).
    return list(dict.fromkeys(candidates))


def _experiment_roots(config_root: Path) -> List[Path]:
    """Return common package/fixture experiment roots without importing Hydra."""
    # Installed nuPlan layout: .../script/config/simulation and
    # .../script/experiments/simulation. The additional roots make tiny local
    # fixtures convenient while keeping lookup deterministic and shallow.
    return list(
        dict.fromkeys(
            [
                config_root.parent.parent / "experiments" / "simulation",
                config_root.parent / "experiments" / "simulation",
                config_root / "experiments" / "simulation",
            ]
        )
    )


def _experiment_candidates(config_root: Path, name: str) -> List[Path]:
    """Return likely local experiment paths for a simple Hydra config name."""
    suffix = Path(name).suffix
    names = [name] if suffix in _YAML_SUFFIXES else [f"{name}.yaml", f"{name}.yml"]
    return [root / candidate for root in _experiment_roots(config_root) for candidate in names]


def _read_config(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Read a config as text and return (text, error), without parsing YAML."""
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return None, f"config is not UTF-8 text: {path}"
    except OSError as exc:
        return None, f"could not read config {path}: {exc}"


def _has_defaults_block(text: str) -> bool:
    """Recognize a top-level-ish Hydra defaults key without YAML evaluation."""
    return bool(re.search(r"(?m)^\s*defaults\s*:", text))


def validate(
    config_root: Path,
    mode: str,
    config_name: Optional[str] = None,
    experiment: Optional[str] = None,
    overrides: Sequence[str] = (),
) -> Tuple[List[str], List[str]]:
    """Return ``(errors, warnings)`` using only deterministic local checks."""
    errors: List[str] = []
    warnings: List[str] = []
    canonical_mode = _canonical_mode(mode)

    if canonical_mode is None:
        errors.append(f"mode must be one of: {', '.join(sorted(MODE_ALIASES))}")

    # Parse overrides even when the root is missing, so one invocation reports
    # all independently actionable input errors.
    parsed_keys: List[str] = []
    for raw in overrides:
        try:
            key, _ = _parse_override(raw)
            parsed_keys.append(key.lstrip("+"))
        except ValueError as exc:
            errors.append(str(exc))

    if not config_root.exists():
        errors.append(f"config root does not exist: {config_root}")
        return errors, warnings
    if not config_root.is_dir():
        errors.append(f"config root is not a directory: {config_root}")
        return errors, warnings

    if canonical_mode is None:
        return errors, warnings

    selected_name = config_name or DEFAULT_CONFIG_NAMES[canonical_mode]
    if "\x00" in selected_name or "\n" in selected_name or "\r" in selected_name:
        errors.append("config name contains a control character")
        config_path = None
    else:
        config_matches = _config_candidates(config_root, selected_name)
        config_path = next((candidate for candidate in config_matches if candidate.is_file()), None)
        if config_path is None:
            expected = ", ".join(str(candidate) for candidate in config_matches)
            errors.append(f"config was not found for {selected_name!r}; checked: {expected}")

    if config_path is not None:
        if config_path.suffix.lower() not in _YAML_SUFFIXES:
            errors.append(f"config must end in .yaml or .yml: {config_path}")
        else:
            text, read_error = _read_config(config_path)
            if read_error:
                errors.append(read_error)
            elif text is not None and not _has_defaults_block(text):
                warnings.append(
                    f"{config_path.name} has no visible Hydra defaults block; inherited groups were not checked"
                )

    if experiment is not None:
        if not _NAME.fullmatch(experiment):
            errors.append("experiment must be a simple config name without path separators")
        elif not any(path.is_file() for path in _experiment_candidates(config_root, experiment)):
            errors.append(f"simulation experiment config was not found: {experiment}")

    if canonical_mode == "simulation" and any(key.endswith("simulation_log_main_path") for key in parsed_keys):
        warnings.append("simulation_log_main_path is set; a fresh simulation entry point requires it to be null")
    if canonical_mode == "metrics" and not any(
        key.endswith("simulation_log_main_path") for key in parsed_keys
    ):
        warnings.append("metrics mode normally needs simulation_log_main_path=<existing-log-root>")
    if canonical_mode == "aggregate" and not any(key.endswith("output_dir") for key in parsed_keys):
        warnings.append("aggregate mode normally needs output_dir=<experiment-output-root>")
    if canonical_mode == "nuboard" and not any(
        key.endswith("simulation_path") for key in parsed_keys
    ):
        warnings.append("nuBoard mode normally needs simulation_path=<descriptor-or-directory>")

    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without importing runtime dependencies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path("."),
        help="directory containing the selected Hydra config group",
    )
    parser.add_argument(
        "--config",
        "--config-name",
        dest="config_name",
        help="config filename or Hydra config name; defaults from --mode",
    )
    parser.add_argument(
        "--experiment",
        "--experiment-name",
        dest="experiment",
        help="simulation experiment config name to find beside the config tree",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_ALIASES),
        default="simulation",
        help="validation mode; aliases are accepted for metric and aggregation entry points",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="opaque Hydra override to syntax-check; repeat for multiple overrides",
    )
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Run the non-executing CLI and return a shell status."""
    args = build_parser().parse_args(argv)
    errors, warnings = validate(
        config_root=args.config_root,
        mode=args.mode,
        config_name=args.config_name,
        experiment=args.experiment,
        overrides=args.override,
    )
    canonical_mode = _canonical_mode(args.mode) or args.mode
    result = {
        "ok": not errors,
        "mode": canonical_mode,
        "config_root": str(args.config_root),
        "errors": errors,
        "warnings": warnings,
        "executed": False,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "OK" if not errors else "ERROR"
        print(f"{status}: non-executing config validation ({canonical_mode})")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("No Hydra composition or runtime action was performed.")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

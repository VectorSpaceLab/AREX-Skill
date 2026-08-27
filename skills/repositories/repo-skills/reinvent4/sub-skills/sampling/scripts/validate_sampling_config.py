#!/usr/bin/env python3
"""Safely validate a REINVENT4 sampling config without running generation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


MODE_CHOICES = (
    "Reinvent",
    "Libinvent",
    "Linkinvent",
    "LibinventTransformer",
    "LinkinventTransformer",
    "Mol2Mol",
    "Pepinvent",
)
TRANSFORMER_MODES = {"Mol2Mol", "LibinventTransformer", "LinkinventTransformer", "Pepinvent"}
SEED_REQUIRED_MODES = {
    "Libinvent",
    "Linkinvent",
    "LibinventTransformer",
    "LinkinventTransformer",
    "Mol2Mol",
    "Pepinvent",
}
REGISTRY_KEYS = {
    ".reinvent",
    ".libinvent",
    ".linkinvent",
    ".m2m_high",
    ".m2m_medium",
    ".m2m_mmp",
    ".m2m_scaffold",
    ".m2m_scaffold_generic",
    ".m2m_similarity",
}
ALLOWED_TOP_LEVEL = {
    "run_type",
    "device",
    "tb_logdir",
    "json_out_config",
    "seed",
    "parameters",
    "filter",
    "responder",
}
ALLOWED_PARAMETERS = {
    "model_file",
    "num_smiles",
    "smiles_file",
    "target_smiles_path",
    "sample_strategy",
    "output_file",
    "target_nll_file",
    "unique_molecules",
    "randomize_smiles",
    "isomeric_smiles",
    "temperature",
}
ALLOWED_FILTER = {"smarts"}


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message


class Validator:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    def info(self, message: str) -> None:
        self.findings.append(Finding("INFO", message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "ERROR" for f in self.findings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a REINVENT4 run_type='sampling' config without loading models or generating SMILES.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("config", type=Path, help="TOML, JSON, or YAML sampling config")
    parser.add_argument(
        "--config-format",
        choices=("auto", "toml", "json", "yaml"),
        default="auto",
        help="Force config format instead of inferring from extension",
    )
    parser.add_argument(
        "--model-mode",
        choices=MODE_CHOICES,
        help="Intended generator mode for static seed-file checks; runtime normally infers this from model_file",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Resolve relative model, seed, and output paths against this directory; defaults to config parent",
    )
    parser.add_argument(
        "--max-total-smiles",
        type=int,
        default=50000,
        help="Warn when requested outputs exceed this no-run safety threshold",
    )
    parser.add_argument(
        "--allow-output-overwrite",
        action="store_true",
        help="Suppress warning when output_file already exists",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary",
    )
    return parser.parse_args()


def load_config(path: Path, fmt: str) -> dict[str, Any]:
    if fmt == "auto":
        suffix = path.suffix.lower().lstrip(".")
        fmt = suffix if suffix in {"toml", "json", "yaml", "yml"} else "toml"
    if fmt == "yml":
        fmt = "yaml"

    if fmt == "toml":
        if tomllib is None:
            raise RuntimeError("TOML parsing requires Python 3.11+ or tomllib availability")
        with path.open("rb") as handle:
            return tomllib.load(handle)
    if fmt == "json":
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if fmt == "yaml":
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError("YAML parsing requires PyYAML; install it or use --config-format toml/json") from exc
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
            return data or {}
    raise RuntimeError(f"Unsupported config format: {fmt}")


def resolve_path(value: str | os.PathLike[str], base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def read_seed_rows(path: Path) -> list[str]:
    rows: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(line)
    return rows


def first_field(row: str) -> str:
    for delimiter in ("\t", ",", " "):
        if delimiter in row:
            return row.split(delimiter, 1)[0].strip()
    return row.strip()


def infer_mode_from_model_file(model_file: str) -> str | None:
    lower = model_file.lower()
    if "linkinvent" in lower:
        return "Linkinvent"
    if "libinvent" in lower:
        return "Libinvent"
    if "mol2mol" in lower or "m2m" in lower:
        return "Mol2Mol"
    if "pepinvent" in lower:
        return "Pepinvent"
    if "reinvent" in lower:
        return "Reinvent"
    return None


def validate_schema(config: dict[str, Any], validator: Validator) -> dict[str, Any]:
    if not isinstance(config, dict):
        validator.error("Config root must be a mapping/object")
        return {}

    unknown_top = sorted(set(config) - ALLOWED_TOP_LEVEL)
    if unknown_top:
        validator.warn(f"Unknown top-level keys for sampling config: {', '.join(unknown_top)}")

    run_type = config.get("run_type")
    if run_type != "sampling":
        validator.error(f"run_type must be 'sampling', found {run_type!r}")

    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        validator.error("Config must contain a [parameters] mapping")
        return {}

    unknown_params = sorted(set(parameters) - ALLOWED_PARAMETERS)
    if unknown_params:
        validator.warn(f"Unknown [parameters] keys for sampling: {', '.join(unknown_params)}")

    filter_section = config.get("filter")
    if filter_section is not None:
        if not isinstance(filter_section, dict):
            validator.error("[filter] must be a mapping when present")
        else:
            unknown_filter = sorted(set(filter_section) - ALLOWED_FILTER)
            if unknown_filter:
                validator.warn(f"Unknown [filter] keys: {', '.join(unknown_filter)}")
            smarts = filter_section.get("smarts")
            if smarts is not None and not isinstance(smarts, list):
                validator.error("[filter].smarts must be a list of SMARTS strings")

    return parameters


def validate_required_parameters(parameters: dict[str, Any], validator: Validator) -> None:
    model_file = parameters.get("model_file")
    if not isinstance(model_file, str) or not model_file.strip():
        validator.error("[parameters].model_file is required and must be a non-empty string")

    num_smiles = parameters.get("num_smiles")
    if not isinstance(num_smiles, int) or isinstance(num_smiles, bool) or num_smiles <= 0:
        validator.error("[parameters].num_smiles is required and must be a positive integer")

    output_file = parameters.get("output_file", "samples.csv")
    if not isinstance(output_file, str) or not output_file.strip():
        validator.error("[parameters].output_file must be a non-empty string when provided")

    for key in ("unique_molecules", "randomize_smiles", "isomeric_smiles"):
        if key in parameters and not isinstance(parameters[key], bool):
            validator.error(f"[parameters].{key} must be boolean")

    if "temperature" in parameters:
        temperature = parameters["temperature"]
        if not isinstance(temperature, (int, float)) or isinstance(temperature, bool) or temperature <= 0:
            validator.error("[parameters].temperature must be a positive number")

    strategy = parameters.get("sample_strategy")
    if strategy not in (None, "", "multinomial", "beamsearch"):
        validator.error("[parameters].sample_strategy should be 'multinomial' or 'beamsearch' when set")


def validate_model_path(model_file: str, base_dir: Path, validator: Validator) -> None:
    if model_file in REGISTRY_KEYS:
        validator.info(f"model_file uses REINVENT4 prior registry key {model_file}; runtime must provide the prior asset")
        return
    if model_file.startswith(".") and model_file not in REGISTRY_KEYS:
        validator.warn(f"model_file {model_file!r} looks like an unknown prior registry key")
        return
    model_path = resolve_path(model_file, base_dir)
    if not model_path.exists():
        validator.warn(f"model_file does not exist at validation time: {model_path}")
    elif not model_path.is_file():
        validator.error(f"model_file is not a file: {model_path}")


def validate_device(config: dict[str, Any], validator: Validator) -> None:
    device = config.get("device", "cpu")
    if not isinstance(device, str) or not device.strip():
        validator.error("device must be a non-empty string when provided")
        return
    if device.startswith("cuda"):
        try:
            import torch  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            validator.warn("device requests CUDA, but PyTorch is not importable for availability check")
            return
        if not torch.cuda.is_available():
            validator.warn("device requests CUDA, but torch.cuda.is_available() is false on this host")


def validate_output_path(parameters: dict[str, Any], base_dir: Path, allow_overwrite: bool, validator: Validator) -> None:
    output_file = parameters.get("output_file", "samples.csv")
    if not isinstance(output_file, str) or not output_file.strip():
        return
    output_path = resolve_path(output_file, base_dir)
    parent = output_path.parent
    if not parent.exists():
        validator.warn(f"output_file parent directory does not exist yet: {parent}")
    if output_path.exists() and not allow_overwrite:
        validator.warn(f"output_file already exists and would be overwritten by REINVENT4: {output_path}")

    target_nll_file = parameters.get("target_nll_file")
    if isinstance(target_nll_file, str) and target_nll_file.strip():
        target_path = resolve_path(target_nll_file, base_dir)
        if target_path.exists() and not allow_overwrite:
            validator.warn(f"target_nll_file already exists and may be overwritten: {target_path}")


def validate_seed_rows(mode: str, rows: list[str], validator: Validator) -> None:
    if mode in {"Libinvent", "LibinventTransformer"}:
        for index, row in enumerate(rows[:10], start=1):
            seed = first_field(row)
            if "*" not in seed:
                validator.warn(f"LibInvent seed row {index} has no attachment point '*': {seed}")
        return

    if mode in {"Linkinvent", "LinkinventTransformer"}:
        for index, row in enumerate(rows[:10], start=1):
            seed = first_field(row)
            if seed.count("|") != 1:
                validator.error(f"LinkInvent seed row {index} must contain exactly one '|' separator: {seed}")
                continue
            left, right = seed.split("|", 1)
            if "*" not in left or "*" not in right:
                validator.warn(f"LinkInvent seed row {index} should have attachment points on both warheads: {seed}")
        return

    if mode == "Mol2Mol":
        for index, row in enumerate(rows[:10], start=1):
            seed = first_field(row)
            if not seed:
                validator.error(f"Mol2Mol seed row {index} has an empty first field")
            if "|" in seed:
                validator.warn(f"Mol2Mol seed row {index} contains '|'; did you mean LinkInvent? {seed}")
        return

    if mode == "Pepinvent":
        for index, row in enumerate(rows[:10], start=1):
            if "?" not in row:
                validator.warn(f"PepInvent seed row {index} has no '?' mask marker: {row}")
        return


def validate_seed_file(
    parameters: dict[str, Any], mode: str | None, base_dir: Path, max_total_smiles: int, validator: Validator
) -> int:
    smiles_file = parameters.get("smiles_file")
    seed_rows = 0

    if mode in SEED_REQUIRED_MODES and not smiles_file:
        validator.error(f"{mode} sampling requires [parameters].smiles_file")
    if mode == "Reinvent" and smiles_file:
        validator.warn("Reinvent de novo sampling usually omits smiles_file; confirm this is intentional")

    if smiles_file:
        if not isinstance(smiles_file, str):
            validator.error("[parameters].smiles_file must be a string path when provided")
            return seed_rows
        seed_path = resolve_path(smiles_file, base_dir)
        if not seed_path.exists():
            validator.error(f"smiles_file does not exist: {seed_path}")
            return seed_rows
        if not seed_path.is_file():
            validator.error(f"smiles_file is not a file: {seed_path}")
            return seed_rows
        rows = read_seed_rows(seed_path)
        seed_rows = len(rows)
        if seed_rows == 0:
            validator.error(f"smiles_file has no non-comment seed rows: {seed_path}")
        elif mode:
            validate_seed_rows(mode, rows, validator)
        validator.info(f"smiles_file contains {seed_rows} non-comment seed row(s)")

    num_smiles = parameters.get("num_smiles")
    if isinstance(num_smiles, int) and not isinstance(num_smiles, bool) and num_smiles > 0:
        multiplier = seed_rows if smiles_file and seed_rows > 0 else 1
        total = num_smiles * multiplier
        validator.info(f"estimated requested outputs before filtering: {total}")
        if total > max_total_smiles:
            validator.warn(
                f"estimated requested outputs {total} exceed --max-total-smiles {max_total_smiles}; reduce num_smiles or seed rows for smoke tests"
            )
        if mode == "Mol2Mol" and parameters.get("sample_strategy") == "beamsearch" and num_smiles > 300:
            validator.warn("Mol2Mol beamsearch with num_smiles > 300 may be very slow")

    return seed_rows


def validate_mode_specific(parameters: dict[str, Any], mode: str | None, validator: Validator) -> None:
    strategy = parameters.get("sample_strategy")
    if mode and mode not in TRANSFORMER_MODES and strategy not in (None, ""):
        validator.warn(f"sample_strategy is only used by transformer modes; {mode} may ignore it")
    if mode in TRANSFORMER_MODES and parameters.get("randomize_smiles") is True:
        validator.warn(f"{mode} is transformer-based; REINVENT4 will set randomize_smiles to false internally")
    if mode in {"Mol2Mol", "Pepinvent"} and strategy in (None, ""):
        validator.warn(f"{mode} usually sets sample_strategy to 'multinomial' or 'beamsearch'")


def build_summary(args: argparse.Namespace, config: dict[str, Any], validator: Validator) -> dict[str, Any]:
    return {
        "config": str(args.config),
        "model_mode": args.model_mode,
        "ok": not validator.has_errors,
        "findings": [{"level": item.level, "message": item.message} for item in validator.findings],
        "run_type": config.get("run_type") if isinstance(config, dict) else None,
        "device": config.get("device") if isinstance(config, dict) else None,
    }


def main() -> int:
    args = parse_args()
    validator = Validator()

    if not args.config.exists():
        validator.error(f"Config file does not exist: {args.config}")
        summary = build_summary(args, {}, validator)
        emit(summary, args.json)
        return 2

    base_dir = (args.base_dir or args.config.parent).resolve()

    try:
        config = load_config(args.config, args.config_format)
    except Exception as exc:  # noqa: BLE001 - command-line validator should report parser failures cleanly
        validator.error(f"Failed to parse config: {exc}")
        summary = build_summary(args, {}, validator)
        emit(summary, args.json)
        return 2

    parameters = validate_schema(config, validator)
    validate_required_parameters(parameters, validator)
    validate_device(config, validator)

    model_file = parameters.get("model_file")
    inferred_mode = infer_mode_from_model_file(model_file) if isinstance(model_file, str) else None
    mode = args.model_mode or inferred_mode
    if args.model_mode and inferred_mode and args.model_mode != inferred_mode:
        validator.warn(f"--model-mode {args.model_mode} differs from model_file name heuristic {inferred_mode}")
    if not mode:
        validator.warn("Could not infer model mode from model_file; pass --model-mode for seed-file shape checks")
    elif not args.model_mode and inferred_mode:
        validator.info(f"inferred model mode from model_file name: {inferred_mode}")

    if isinstance(model_file, str):
        validate_model_path(model_file, base_dir, validator)
    validate_output_path(parameters, base_dir, args.allow_output_overwrite, validator)
    validate_seed_file(parameters, mode, base_dir, args.max_total_smiles, validator)
    validate_mode_specific(parameters, mode, validator)

    summary = build_summary(args, config, validator)
    emit(summary, args.json)
    return 1 if validator.has_errors else 0


def emit(summary: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    status = "OK" if summary["ok"] else "FAILED"
    print(f"Sampling config validation: {status}")
    for finding in summary["findings"]:
        print(f"[{finding['level']}] {finding['message']}")


if __name__ == "__main__":
    sys.exit(main())

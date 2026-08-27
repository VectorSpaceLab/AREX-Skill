#!/usr/bin/env python3
"""Static checks for REINVENT4 transfer_learning and staged_learning configs.

The script parses TOML, JSON, or YAML and checks high-level sections, required
paths, stage scoring references, and common risky settings. It does not import
REINVENT4 and does not start training.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    tomllib = None  # type: ignore[assignment]


ALLOWED_RUN_TYPES = {"transfer_learning", "staged_learning"}
RL_DIVERSITY_TYPES = {
    "IdenticalMurckoScaffold",
    "IdenticalTopologicalScaffold",
    "ScaffoldSimilarity",
    "PenalizeSameSmiles",
}
RL_INTRINSIC_TYPES = {"IdenticalMurckoScaffoldRND"}
RL_PENALTY_FUNCTIONS = {"Step", "Sigmoid", "Linear", "Tanh", "Erf"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARN: {message}")
        for message in self.notes:
            print(f"OK: {message}")


def load_config(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    data = path.read_bytes()

    if suffix == ".json":
        return json.loads(data.decode("utf-8"))

    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError("YAML config requires PyYAML to be installed") from exc
        loaded = yaml.safe_load(data.decode("utf-8"))
        return loaded or {}

    if tomllib is None:
        raise RuntimeError("TOML config requires Python 3.11+ tomllib")
    return tomllib.loads(data.decode("utf-8"))


def as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def resolve_path(config_path: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(os.path.expanduser(value))
    if not candidate.is_absolute():
        candidate = config_path.parent / candidate
    return candidate


def check_existing_path(
    reporter: Reporter,
    config_path: Path,
    section: str,
    key: str,
    value: Any,
    *,
    required: bool = True,
) -> None:
    path = resolve_path(config_path, value)
    if path is None:
        if required:
            reporter.error(f"{section}.{key} is required")
        return
    if not path.exists():
        reporter.warn(f"{section}.{key} points to missing path: {value}")
    else:
        reporter.note(f"{section}.{key} exists: {value}")


def check_positive_int(reporter: Reporter, section: str, key: str, value: Any, *, required: bool) -> None:
    if value is None:
        if required:
            reporter.error(f"{section}.{key} is required")
        return
    if not isinstance(value, int) or value < 1:
        reporter.error(f"{section}.{key} should be an integer >= 1")


def check_score(reporter: Reporter, section: str, key: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        reporter.error(f"{section}.{key} should be between 0 and 1")


def check_device(reporter: Reporter, config: dict[str, Any]) -> None:
    device = config.get("device", "cpu")
    if isinstance(device, str) and device.startswith("cuda"):
        reporter.warn(
            "config requests CUDA; use 'reinvent --device cpu CONFIG' for CPU fallback if CUDA is unavailable"
        )
    elif device == "cpu" or device is None:
        reporter.note("device is CPU or unspecified")
    else:
        reporter.warn(f"device is unusual for REINVENT4 learning runs: {device!r}")

    if "tb_logdir" in as_mapping(config.get("parameters")):
        reporter.warn("tb_logdir appears under [parameters]; REINVENT4 learning configs use top-level tb_logdir")


def check_transfer_learning(reporter: Reporter, config_path: Path, config: dict[str, Any]) -> None:
    params = as_mapping(config.get("parameters"))
    if not params:
        reporter.error("[parameters] section is required for transfer_learning")
        return

    for key in ("input_model_file", "smiles_file"):
        check_existing_path(reporter, config_path, "parameters", key, params.get(key))

    if not isinstance(params.get("output_model_file"), str) or not params.get("output_model_file"):
        reporter.error("parameters.output_model_file is required")
    else:
        output_path = resolve_path(config_path, params.get("output_model_file"))
        if output_path and output_path.exists():
            reporter.warn(f"parameters.output_model_file already exists and may be overwritten: {params['output_model_file']}")
        else:
            reporter.note("parameters.output_model_file is set")

    check_existing_path(
        reporter,
        config_path,
        "parameters",
        "validation_smiles_file",
        params.get("validation_smiles_file"),
        required=False,
    )
    if not params.get("validation_smiles_file"):
        reporter.warn("validation_smiles_file is absent; validation loss will not be available")

    check_positive_int(reporter, "parameters", "num_epochs", params.get("num_epochs"), required=True)
    check_positive_int(reporter, "parameters", "batch_size", params.get("batch_size"), required=True)
    check_positive_int(
        reporter,
        "parameters",
        "save_every_n_epochs",
        params.get("save_every_n_epochs", 1),
        required=False,
    )

    if params.get("num_epochs", 0) and isinstance(params.get("num_epochs"), int) and params["num_epochs"] > 200:
        reporter.warn("num_epochs is high; confirm long TL runtime and overfitting monitoring")

    pairs = params.get("pairs")
    dotted_pairs = {key: value for key, value in params.items() if key.startswith("pairs.")}
    if pairs or dotted_pairs:
        reporter.note("Mol2Mol-style pair settings detected")
    else:
        reporter.warn("no pairs settings detected; this is fine for Reinvent TL but usually incomplete for Mol2Mol TL")


def check_diversity_filter(reporter: Reporter, section_name: str, config: dict[str, Any]) -> None:
    filter_type = config.get("type")
    if not filter_type:
        reporter.error(f"{section_name}.type is required")
    elif filter_type not in RL_DIVERSITY_TYPES:
        reporter.warn(f"{section_name}.type is not one of the common REINVENT4 filters: {filter_type}")

    if "bucket_size" in config:
        check_positive_int(reporter, section_name, "bucket_size", config.get("bucket_size"), required=False)
    for key in ("minscore", "minsimilarity", "penalty_multiplier"):
        if key in config:
            check_score(reporter, section_name, key, config.get(key))


def check_stage_scoring(reporter: Reporter, config_path: Path, stage: dict[str, Any], index: int) -> None:
    scoring = as_mapping(stage.get("scoring"))
    label = f"stage[{index}].scoring"
    if not scoring:
        reporter.error(f"{label} is required")
        return

    filename = scoring.get("filename")
    if filename:
        check_existing_path(reporter, config_path, label, "filename", filename)
        filetype = scoring.get("filetype")
        if not filetype:
            reporter.warn(f"{label}.filename is set but filetype is absent; add 'toml' or 'json' for clarity")
        elif str(filetype).lower() not in {"toml", "json", "yaml", "yml"}:
            reporter.warn(f"{label}.filetype is unusual: {filetype}")
    elif not scoring.get("component"):
        reporter.warn(f"{label} has no filename and no inline component list")

    aggregation = scoring.get("type")
    if not aggregation:
        reporter.warn(f"{label}.type is absent; add an aggregation such as geometric_mean")


def check_staged_learning(reporter: Reporter, config_path: Path, config: dict[str, Any]) -> None:
    params = as_mapping(config.get("parameters"))
    if not params:
        reporter.error("[parameters] section is required for staged_learning")
        return

    for key in ("prior_file", "agent_file"):
        check_existing_path(reporter, config_path, "parameters", key, params.get(key))

    if not params.get("summary_csv_prefix"):
        reporter.warn("parameters.summary_csv_prefix is absent; REINVENT4 defaults to 'summary'")
    elif isinstance(params.get("summary_csv_prefix"), str):
        csv_prefix = resolve_path(config_path, f"{params['summary_csv_prefix']}_1.csv")
        if csv_prefix and csv_prefix.exists():
            reporter.warn(f"stage CSV may already exist and be appended/overwritten: {csv_prefix.name}")

    check_positive_int(reporter, "parameters", "batch_size", params.get("batch_size", 100), required=False)
    if params.get("smiles_file"):
        check_existing_path(reporter, config_path, "parameters", "smiles_file", params.get("smiles_file"), required=False)

    strategy = as_mapping(config.get("learning_strategy"))
    if not strategy:
        reporter.warn("[learning_strategy] is absent; defaults are type='dap', sigma=128, rate=0.0001")
    else:
        if strategy.get("type", "dap") != "dap":
            reporter.warn("learning_strategy.type is not 'dap'; DAP is the standard supported strategy")
        sigma = strategy.get("sigma", 128)
        if not isinstance(sigma, int) or sigma < 1:
            reporter.error("learning_strategy.sigma should be an integer >= 1")
        elif sigma > 256:
            reporter.warn("learning_strategy.sigma is high; confirm divergence and diversity safeguards")
        rate = strategy.get("rate", 0.0001)
        if not isinstance(rate, (int, float)) or float(rate) <= 0:
            reporter.error("learning_strategy.rate should be positive")

    diversity_filter = as_mapping(config.get("diversity_filter"))
    if diversity_filter:
        check_diversity_filter(reporter, "diversity_filter", diversity_filter)
        reporter.note("global diversity_filter is configured and will override stage diversity filters")

    intrinsic = as_mapping(config.get("intrinsic_penalty"))
    if intrinsic:
        intrinsic_type = intrinsic.get("type")
        if intrinsic_type not in RL_INTRINSIC_TYPES:
            reporter.warn(f"intrinsic_penalty.type is not a common REINVENT4 type: {intrinsic_type}")
        penalty_function = intrinsic.get("penalty_function")
        if penalty_function not in RL_PENALTY_FUNCTIONS:
            reporter.warn(f"intrinsic_penalty.penalty_function is unusual: {penalty_function}")
        if diversity_filter:
            reporter.warn("global diversity_filter takes precedence over intrinsic_penalty")

    inception = as_mapping(config.get("inception"))
    if inception:
        check_existing_path(
            reporter,
            config_path,
            "inception",
            "smiles_file",
            inception.get("smiles_file"),
            required=False,
        )
        check_positive_int(reporter, "inception", "memory_size", inception.get("memory_size", 50), required=False)
        check_positive_int(reporter, "inception", "sample_size", inception.get("sample_size", 10), required=False)

    stages = as_list(config.get("stage"))
    if not stages:
        reporter.error("at least one [[stage]] block is required")
        return

    for index, raw_stage in enumerate(stages, start=1):
        stage = as_mapping(raw_stage)
        label = f"stage[{index}]"
        if not stage:
            reporter.error(f"{label} should be a mapping")
            continue
        check_positive_int(reporter, label, "max_steps", stage.get("max_steps"), required=True)
        check_positive_int(reporter, label, "min_steps", stage.get("min_steps", 50), required=False)
        check_score(reporter, label, "max_score", stage.get("max_score", 1.0))
        if stage.get("termination", "simple") != "simple":
            reporter.warn(f"{label}.termination is not 'simple'; confirm terminator support")
        if not stage.get("chkpt_file"):
            reporter.warn(f"{label}.chkpt_file is absent; add one for recovery and TL-then-RL handoff")
        check_stage_scoring(reporter, config_path, stage, index)
        stage_filter = as_mapping(stage.get("diversity_filter"))
        if stage_filter:
            check_diversity_filter(reporter, f"{label}.diversity_filter", stage_filter)
            if diversity_filter:
                reporter.warn(f"{label}.diversity_filter will be ignored because global diversity_filter is set")
        if isinstance(stage.get("max_steps"), int) and stage["max_steps"] > 1000:
            reporter.warn(f"{label}.max_steps is high; confirm long RL runtime before launching")


def check_config(config_path: Path, config: dict[str, Any]) -> Reporter:
    reporter = Reporter()
    run_type = config.get("run_type")

    if run_type not in ALLOWED_RUN_TYPES:
        reporter.error(f"run_type must be one of {sorted(ALLOWED_RUN_TYPES)}, got {run_type!r}")
        return reporter

    reporter.note(f"run_type is {run_type}")
    check_device(reporter, config)

    if run_type == "transfer_learning":
        check_transfer_learning(reporter, config_path, config)
    elif run_type == "staged_learning":
        check_staged_learning(reporter, config_path, config)

    return reporter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="REINVENT4 learning config in TOML, JSON, or YAML format")
    args = parser.parse_args(argv)

    config_path = args.config.expanduser().resolve()
    if not config_path.exists():
        print(f"ERROR: config file does not exist: {args.config}")
        return 2

    try:
        loaded = load_config(config_path)
    except Exception as exc:  # noqa: BLE001 - CLI should show parse failure cleanly
        print(f"ERROR: failed to parse {args.config}: {exc}")
        return 2

    if not isinstance(loaded, dict):
        print(f"ERROR: top-level config must be a mapping, got {type(loaded).__name__}")
        return 2

    reporter = check_config(config_path, loaded)
    reporter.print()

    if reporter.errors:
        print(f"SUMMARY: failed with {len(reporter.errors)} error(s) and {len(reporter.warnings)} warning(s)")
        return 1

    print(f"SUMMARY: passed with {len(reporter.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate SaProt task YAML paths and backend choices without heavy ML imports."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

try:
    import lmdb
except ImportError:  # pragma: no cover - optional strict LMDB checks degrade gracefully
    lmdb = None  # type: ignore[assignment]

MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(/[A-Za-z_][A-Za-z0-9_]*)*$")
LMDB_KEYS = ("train_lmdb", "valid_lmdb", "test_lmdb")


class Reporter:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    def print(self) -> None:
        for message in self.info:
            print(f"INFO: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        for message in self.errors:
            print(f"ERROR: {message}")
        if self.errors:
            print(f"\nValidation failed with {len(self.errors)} error(s) and {len(self.warnings)} warning(s).")
        else:
            print(f"\nValidation passed with {len(self.warnings)} warning(s).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically validate a SaProt task YAML without importing model, dataset, torch, or transformers modules."
    )
    parser.add_argument("--config", required=True, type=Path, help="Path to a SaProt YAML config.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="Run base for resolving relative model, dataset, LMDB, tokenizer, and checkpoint paths.",
    )
    parser.add_argument(
        "--require-assets",
        action="store_true",
        help="Treat missing LMDB and model/tokenizer asset paths as errors instead of warnings.",
    )
    parser.add_argument(
        "--skip-lmdb-open",
        action="store_true",
        help="Only check LMDB directory shape; do not open LMDB environments to read length.",
    )
    return parser.parse_args()


def load_yaml(path: Path, reporter: Reporter) -> Optional[Mapping[str, Any]]:
    if not path.is_file():
        reporter.error(f"config file does not exist: {path}")
        return None
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        reporter.error("Missing dependency 'PyYAML'. Install pyyaml before validating config files.")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        reporter.error(f"YAML parse failed: {exc}")
        return None
    if not isinstance(data, dict):
        reporter.error("config root must be a YAML mapping")
        return None
    return data


def as_mapping(value: Any, name: str, reporter: Reporter) -> Mapping[str, Any]:
    if isinstance(value, dict):
        return value
    reporter.error(f"{name} must be a mapping")
    return {}


def resolve_path(base_dir: Path, raw_path: Any) -> Optional[Path]:
    if raw_path is None:
        return None
    if not isinstance(raw_path, str):
        return None
    expanded = Path(os.path.expanduser(os.path.expandvars(raw_path)))
    if expanded.is_absolute():
        return expanded
    return base_dir / expanded


def check_module_path(section_name: str, raw_value: Any, root_name: str, base_dir: Path, reporter: Reporter) -> None:
    if not isinstance(raw_value, str) or not raw_value:
        reporter.error(f"{section_name} must be a non-empty string")
        return
    if raw_value.endswith(".py"):
        reporter.error(f"{section_name} should omit the .py suffix: {raw_value}")
    if raw_value.startswith(f"{root_name}/"):
        reporter.error(f"{section_name} should be relative to {root_name}/, not start with {root_name}/: {raw_value}")
    if not MODULE_RE.match(raw_value.replace(".py", "")):
        reporter.error(f"{section_name} should use slash-separated Python identifiers: {raw_value}")
        return
    candidate = base_dir / root_name / f"{raw_value}.py"
    if candidate.exists():
        reporter.note(f"resolved {section_name} -> {candidate}")
    else:
        reporter.warn(f"could not find {section_name} target at {candidate}")


def check_asset_path(name: str, raw_value: Any, base_dir: Path, require_assets: bool, reporter: Reporter) -> None:
    if raw_value is None:
        return
    if not isinstance(raw_value, str) or not raw_value:
        reporter.error(f"{name} must be a non-empty path string when provided")
        return
    resolved = resolve_path(base_dir, raw_value)
    if resolved is None:
        reporter.error(f"{name} could not be resolved: {raw_value!r}")
        return
    if resolved.exists():
        reporter.note(f"resolved {name} -> {resolved}")
    elif require_assets:
        reporter.error(f"missing required asset path for {name}: {resolved}")
    else:
        reporter.warn(f"asset path for {name} does not exist yet: {resolved}")


def check_lmdb_path(name: str, raw_value: Any, base_dir: Path, require_assets: bool, skip_open: bool, reporter: Reporter) -> None:
    if raw_value is None:
        reporter.warn(f"dataset.{name} is not set")
        return
    if not isinstance(raw_value, str) or not raw_value:
        reporter.error(f"dataset.{name} must be a non-empty path string")
        return
    resolved = resolve_path(base_dir, raw_value)
    if resolved is None:
        reporter.error(f"dataset.{name} could not be resolved: {raw_value!r}")
        return
    if not resolved.exists():
        if require_assets:
            reporter.error(f"missing required LMDB path for dataset.{name}: {resolved}")
        else:
            reporter.warn(f"LMDB path for dataset.{name} does not exist yet: {resolved}")
        return
    if not resolved.is_dir():
        reporter.error(f"dataset.{name} is not a directory: {resolved}")
        return

    data_file = resolved / "data.mdb"
    lock_file = resolved / "lock.mdb"
    if not data_file.exists():
        reporter.warn(f"dataset.{name} directory exists but data.mdb is missing: {resolved}")
    if not lock_file.exists():
        reporter.warn(f"dataset.{name} directory exists but lock.mdb is missing: {resolved}")
    if skip_open:
        return
    if lmdb is None:
        reporter.warn("python package 'lmdb' is unavailable; skipping LMDB length-key check")
        return
    try:
        env = lmdb.open(str(resolved), readonly=True, lock=False, max_readers=1)
        try:
            with env.begin() as txn:
                raw_length = txn.get(b"length")
                if raw_length is None:
                    reporter.error(f"dataset.{name} is missing required LMDB key: length")
                else:
                    length_text = raw_length.decode("utf-8")
                    length = int(length_text)
                    reporter.note(f"dataset.{name} length -> {length}")
                    if length > 0 and txn.get(b"0") is None:
                        reporter.error(f"dataset.{name} length is positive but numeric key 0 is missing")
        finally:
            env.close()
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
        reporter.error(f"could not open dataset.{name} as LMDB: {exc}")


def parse_visible_devices(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "~"}:
        return None
    return len([item for item in text.split(",") if item.strip()])


def parse_device_count(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
        if "," in stripped:
            return len([item for item in stripped.split(",") if item.strip()])
    if isinstance(value, list):
        return len(value)
    return None


def check_trainer(trainer: Mapping[str, Any], setting: Mapping[str, Any], reporter: Reporter) -> None:
    accelerator = trainer.get("accelerator")
    devices = trainer.get("devices")
    precision = trainer.get("precision")
    strategy = trainer.get("strategy")
    device_count = parse_device_count(devices)

    if accelerator not in {None, "cpu", "gpu", "cuda", "auto", "mps", "tpu"}:
        reporter.warn(f"Trainer.accelerator has an uncommon value: {accelerator!r}")
    if device_count is None and devices is not None:
        reporter.warn(f"Trainer.devices could not be interpreted statically: {devices!r}")
    if accelerator == "cpu":
        if device_count not in {None, 1}:
            reporter.warn("CPU smoke configs usually use Trainer.devices: 1")
        if precision in {16, "16", "16-mixed", "bf16", "bf16-mixed"}:
            reporter.warn("CPU configs usually use 32-bit precision instead of 16-bit or bf16 precision")
    if accelerator in {"gpu", "cuda"}:
        os_environ = as_mapping(setting.get("os_environ", {}), "setting.os_environ", reporter)
        visible_count = parse_visible_devices(os_environ.get("CUDA_VISIBLE_DEVICES"))
        if visible_count is not None and device_count is not None and device_count > visible_count:
            reporter.error(
                f"Trainer.devices requests {device_count} GPU(s), but CUDA_VISIBLE_DEVICES exposes {visible_count}"
            )
        if device_count is None:
            reporter.warn("GPU config should make Trainer.devices explicit for reproducibility")
    if isinstance(strategy, dict) and "find_unused_parameters" in strategy:
        reporter.note(f"Trainer.strategy.find_unused_parameters -> {strategy['find_unused_parameters']}")


def check_dataset_kwargs(dataset: Mapping[str, Any], reporter: Reporter) -> None:
    kwargs = as_mapping(dataset.get("kwargs", {}), "dataset.kwargs", reporter)
    dataset_path = dataset.get("dataset_py_path")
    if kwargs.get("plddt_threshold") is not None:
        if dataset_path == "saprot/saprot_ppi_dataset":
            reporter.note("pLDDT threshold requires row fields plddt_1 and plddt_2 for PPI data")
        else:
            reporter.note("pLDDT threshold requires row field plddt aligned with tokenized seq")
    if kwargs.get("use_bias_feature") is True:
        reporter.note("use_bias_feature requires row field coords for supported dataset classes")
    dataloader_kwargs = as_mapping(dataset.get("dataloader_kwargs", {}), "dataset.dataloader_kwargs", reporter)
    if dataloader_kwargs.get("num_workers") not in {None, 0}:
        reporter.warn("For CPU smoke tests or notebooks, consider dataset.dataloader_kwargs.num_workers: 0")


def main() -> int:
    args = parse_args()
    reporter = Reporter()
    base_dir = args.base_dir.resolve()
    reporter.note(f"base directory -> {base_dir}")

    config = load_yaml(args.config, reporter)
    if config is None:
        reporter.print()
        return 1

    for section in ("setting", "model", "dataset", "Trainer"):
        if section not in config:
            reporter.error(f"missing required top-level section: {section}")

    setting = as_mapping(config.get("setting", {}), "setting", reporter)
    model = as_mapping(config.get("model", {}), "model", reporter)
    dataset = as_mapping(config.get("dataset", {}), "dataset", reporter)
    trainer = as_mapping(config.get("Trainer", {}), "Trainer", reporter)

    check_module_path("model.model_py_path", model.get("model_py_path"), "model", base_dir, reporter)
    check_module_path("dataset.dataset_py_path", dataset.get("dataset_py_path"), "dataset", base_dir, reporter)

    model_kwargs = as_mapping(model.get("kwargs", {}), "model.kwargs", reporter)
    dataset_kwargs = as_mapping(dataset.get("kwargs", {}), "dataset.kwargs", reporter)
    check_asset_path("model.kwargs.config_path", model_kwargs.get("config_path"), base_dir, args.require_assets, reporter)
    check_asset_path("model.kwargs.lora_config_path", model_kwargs.get("lora_config_path"), base_dir, args.require_assets, reporter)
    check_asset_path("dataset.kwargs.tokenizer", dataset_kwargs.get("tokenizer"), base_dir, args.require_assets, reporter)
    check_asset_path("model.save_path parent", str(Path(model["save_path"]).parent) if isinstance(model.get("save_path"), str) else None, base_dir, False, reporter)

    for key in LMDB_KEYS:
        check_lmdb_path(key, dataset.get(key), base_dir, args.require_assets, args.skip_lmdb_open, reporter)

    check_dataset_kwargs(dataset, reporter)
    check_trainer(trainer, setting, reporter)

    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())

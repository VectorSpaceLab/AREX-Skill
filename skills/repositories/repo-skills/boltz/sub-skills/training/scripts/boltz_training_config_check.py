#!/usr/bin/env python3
"""Static validator for Boltz training configuration files."""

from __future__ import annotations

import argparse
import importlib
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLACEHOLDER_TOKENS = (
    "SET_PATH_HERE",
    "PATH_TO_",
    "YOUR_",
    "TODO",
    "CHANGEME",
)

OPTIONAL_PATH_KEYS = {"resume", "pretrained", "split", "manifest_path"}
REQUIRED_DATASET_PATH_KEYS = {"target_dir", "msa_dir"}


@dataclass
class Finding:
    level: str
    path: str
    message: str


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value == "{}":
        return {}
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def split_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise ValueError(f"expected key/value entry, got {content!r}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"empty key in {content!r}")
    return key, value.strip()


def yaml_subset_load(path: Path) -> Any:
    """Parse the YAML subset used by Boltz training configs.

    PyYAML is preferred when installed. This fallback supports nested mappings,
    lists of mappings, comments, quoted strings, booleans, nulls, and numeric
    scalars so the checker remains usable in lean Python environments.
    """

    lines: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
                raise ValueError(f"tabs in indentation are unsupported at line {line_number}")
            stripped_comment = strip_yaml_comment(raw_line)
            if not stripped_comment.strip():
                continue
            indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
            lines.append((indent, stripped_comment.lstrip(" ")))

    if not lines:
        return None

    def parse_block(position: int, indent: int) -> tuple[Any, int]:
        if position >= len(lines) or lines[position][0] < indent:
            return {}, position
        if lines[position][0] != indent:
            indent = lines[position][0]
        if lines[position][1].startswith("- "):
            return parse_list(position, indent)
        return parse_mapping(position, indent)

    def parse_mapping(position: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while position < len(lines):
            line_indent, content = lines[position]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise ValueError(f"unexpected indentation near {content!r}")
            if content.startswith("- "):
                break

            key, raw_value = split_key_value(content)
            if raw_value == "":
                if position + 1 < len(lines) and lines[position + 1][0] > line_indent:
                    result[key], position = parse_block(position + 1, lines[position + 1][0])
                else:
                    result[key] = {}
                    position += 1
            else:
                result[key] = parse_scalar(raw_value)
                position += 1
        return result, position

    def parse_list(position: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while position < len(lines):
            line_indent, content = lines[position]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise ValueError(f"unexpected indentation near {content!r}")
            if not content.startswith("- "):
                break

            item = content[2:].strip()
            if item == "":
                if position + 1 < len(lines) and lines[position + 1][0] > line_indent:
                    child, position = parse_block(position + 1, lines[position + 1][0])
                else:
                    child = None
                    position += 1
                result.append(child)
                continue

            if ":" in item and not item.startswith(("'", '"')):
                key, raw_value = split_key_value(item)
                child_map: dict[str, Any] = {}
                if raw_value == "":
                    if position + 1 < len(lines) and lines[position + 1][0] > line_indent:
                        child_map[key], position = parse_block(position + 1, lines[position + 1][0])
                    else:
                        child_map[key] = {}
                        position += 1
                else:
                    child_map[key] = parse_scalar(raw_value)
                    position += 1

                if position < len(lines) and lines[position][0] > line_indent:
                    extra, position = parse_block(position, lines[position][0])
                    if isinstance(extra, dict):
                        child_map.update(extra)
                    else:
                        raise ValueError(f"list item mapping cannot merge {type(extra).__name__}")
                result.append(child_map)
            else:
                result.append(parse_scalar(item))
                position += 1
        return result, position

    parsed, final_position = parse_block(0, lines[0][0])
    if final_position != len(lines):
        raise ValueError(f"could not parse YAML near {lines[final_position][1]!r}")
    return parsed


def load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError:
        try:
            return yaml_subset_load(path)
        except ValueError as exc:
            raise SystemExit(
                "PyYAML is not installed and the built-in YAML subset parser could not parse this config: "
                f"{exc}"
            ) from exc

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def add(findings: list[Finding], level: str, path: str, message: str) -> None:
    findings.append(Finding(level, path, message))


def is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(token in value for token in PLACEHOLDER_TOKENS)


def is_empty(value: Any) -> bool:
    return value is None or value == ""


def as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def resolve_path(value: str, base_dir: Path) -> Path:
    raw = Path(value).expanduser()
    if raw.is_absolute():
        return raw
    return (base_dir / raw).resolve()


def path_should_exist(key: str, value: Any) -> bool:
    if is_empty(value) or is_placeholder(value) or not isinstance(value, str):
        return False
    if value.startswith(("s3://", "gs://", "http://", "https://")):
        return False
    return key in OPTIONAL_PATH_KEYS or key in REQUIRED_DATASET_PATH_KEYS or key == "symmetries"


def walk_placeholders(value: Any, path: str, findings: list[Finding]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            walk_placeholders(item, child, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk_placeholders(item, f"{path}[{index}]", findings)
    elif is_placeholder(value):
        add(findings, "ERROR", path, f"placeholder value remains: {value!r}")


def collect_targets(value: Any, path: str = "") -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            if key == "_target_" and isinstance(item, str):
                targets.append((child, item))
            else:
                targets.extend(collect_targets(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            targets.extend(collect_targets(item, f"{path}[{index}]"))
    return targets


def import_target(target: str) -> tuple[bool, str | None]:
    module_name, sep, attr_name = target.rpartition(".")
    if not sep:
        return False, "target is not a dotted import path"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        return False, f"module import failed: {type(exc).__name__}: {exc}"
    if not hasattr(module, attr_name):
        return False, f"module imports but attribute {attr_name!r} is missing"
    return True, None


def check_top_level(config: Any, findings: list[Finding]) -> None:
    if not isinstance(config, dict):
        add(findings, "ERROR", "config", "top-level YAML must be a mapping")
        return
    for key in ("data", "model", "output"):
        if key not in config:
            add(findings, "ERROR", key, "required top-level field is missing")
    if "trainer" not in config:
        add(findings, "WARN", "trainer", "trainer block is absent; PyTorch Lightning defaults will be used")


def check_paths(config: dict[str, Any], config_dir: Path, findings: list[Finding]) -> None:
    output = config.get("output")
    if is_empty(output):
        add(findings, "ERROR", "output", "output directory is required")
    elif isinstance(output, str) and not is_placeholder(output):
        output_path = resolve_path(output, config_dir)
        parent = output_path if output_path.exists() and output_path.is_dir() else output_path.parent
        if not parent.exists():
            add(findings, "WARN", "output", f"output parent does not exist yet: {parent}")
    elif not isinstance(output, str):
        add(findings, "ERROR", "output", "output must be a path string")

    for key in ("resume", "pretrained"):
        value = config.get(key)
        if path_should_exist(key, value):
            resolved = resolve_path(value, config_dir)
            if not resolved.exists():
                add(findings, "WARN", key, f"checkpoint path does not exist: {resolved}")

    data = as_mapping(config.get("data"))
    symmetries = data.get("symmetries")
    if is_empty(symmetries):
        add(findings, "ERROR", "data.symmetries", "symmetry pickle path is required")
    elif path_should_exist("symmetries", symmetries):
        resolved = resolve_path(symmetries, config_dir)
        if not resolved.exists():
            add(findings, "ERROR", "data.symmetries", f"symmetry file does not exist: {resolved}")
        elif resolved.is_dir():
            add(findings, "ERROR", "data.symmetries", f"expected a file, got directory: {resolved}")


def check_datasets(config: dict[str, Any], config_dir: Path, findings: list[Finding]) -> None:
    data = as_mapping(config.get("data"))
    datasets = data.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        add(findings, "ERROR", "data.datasets", "must be a non-empty list")
        return

    probabilities: list[float] = []
    for index, dataset in enumerate(datasets):
        path = f"data.datasets[{index}]"
        if not isinstance(dataset, dict):
            add(findings, "ERROR", path, "dataset entry must be a mapping")
            continue

        for key in ("target_dir", "msa_dir", "prob", "sampler", "cropper"):
            if key not in dataset:
                add(findings, "ERROR", f"{path}.{key}", "dataset field is missing")

        prob = dataset.get("prob")
        if isinstance(prob, (int, float)) and not isinstance(prob, bool):
            probabilities.append(float(prob))
            if prob <= 0:
                add(findings, "ERROR", f"{path}.prob", "dataset probability must be positive")
        elif prob is not None:
            add(findings, "ERROR", f"{path}.prob", "dataset probability must be numeric")

        target_dir = dataset.get("target_dir")
        if is_empty(target_dir):
            add(findings, "ERROR", f"{path}.target_dir", "processed target directory is required")
        elif path_should_exist("target_dir", target_dir):
            resolved = resolve_path(target_dir, config_dir)
            if not resolved.exists():
                add(findings, "ERROR", f"{path}.target_dir", f"target directory does not exist: {resolved}")
            elif not resolved.is_dir():
                add(findings, "ERROR", f"{path}.target_dir", f"target path is not a directory: {resolved}")
            else:
                manifest_path = dataset.get("manifest_path")
                resolved_manifest = (
                    resolve_path(manifest_path, config_dir)
                    if path_should_exist("manifest_path", manifest_path)
                    else resolved / "manifest.json"
                )
                if not resolved_manifest.exists():
                    add(findings, "ERROR", f"{path}.manifest", f"manifest file does not exist: {resolved_manifest}")
                structures = resolved / "structures"
                if not structures.exists():
                    add(findings, "WARN", f"{path}.target_dir", f"structures subdirectory not found: {structures}")

        msa_dir = dataset.get("msa_dir")
        if is_empty(msa_dir):
            add(findings, "ERROR", f"{path}.msa_dir", "processed MSA directory is required")
        elif path_should_exist("msa_dir", msa_dir):
            resolved = resolve_path(msa_dir, config_dir)
            if not resolved.exists():
                add(findings, "ERROR", f"{path}.msa_dir", f"MSA directory does not exist: {resolved}")
            elif not resolved.is_dir():
                add(findings, "ERROR", f"{path}.msa_dir", f"MSA path is not a directory: {resolved}")

        split = dataset.get("split")
        if path_should_exist("split", split):
            resolved = resolve_path(split, config_dir)
            if not resolved.exists():
                add(findings, "ERROR", f"{path}.split", f"split file does not exist: {resolved}")
            elif resolved.is_dir():
                add(findings, "ERROR", f"{path}.split", f"expected split file, got directory: {resolved}")
            elif resolved.stat().st_size == 0:
                add(findings, "WARN", f"{path}.split", "split file is empty; validation set may be empty")

    if probabilities:
        total = sum(probabilities)
        if not math.isclose(total, 1.0, rel_tol=1e-3, abs_tol=1e-3):
            add(findings, "WARN", "data.datasets[*].prob", f"dataset probabilities sum to {total:g}, not 1.0")


def check_numeric(config: dict[str, Any], profile: str, findings: list[Finding]) -> None:
    data = as_mapping(config.get("data"))
    trainer = as_mapping(config.get("trainer"))
    model = as_mapping(config.get("model"))
    training_args = as_mapping(model.get("training_args"))

    positive_data_fields = (
        "max_tokens",
        "max_atoms",
        "max_seqs",
        "samples_per_epoch",
        "batch_size",
        "num_workers",
        "atoms_per_window_queries",
        "num_bins",
    )
    for key in positive_data_fields:
        value = data.get(key)
        if value is None:
            add(findings, "WARN", f"data.{key}", "field is absent; verify dataclass defaults or config intent")
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            add(findings, "ERROR", f"data.{key}", "must be an integer")
            continue
        if key == "num_workers":
            if value < 0:
                add(findings, "ERROR", f"data.{key}", "must be nonnegative")
        elif value <= 0:
            add(findings, "ERROR", f"data.{key}", "must be positive")

    if data.get("val_batch_size", 1) != 1:
        add(findings, "ERROR", "data.val_batch_size", "Boltz validation asserts val_batch_size == 1")

    min_dist = data.get("min_dist")
    max_dist = data.get("max_dist")
    if isinstance(min_dist, (int, float)) and isinstance(max_dist, (int, float)) and min_dist >= max_dist:
        add(findings, "ERROR", "data.min_dist", "min_dist must be smaller than max_dist")

    warmup = training_args.get("lr_warmup_no_steps")
    start_decay = training_args.get("lr_start_decay_after_n_steps")
    decay_every = training_args.get("lr_decay_every_n_steps")
    if isinstance(warmup, int) and isinstance(start_decay, int) and warmup > start_decay:
        add(findings, "ERROR", "model.training_args.lr_warmup_no_steps", "warmup must not exceed start_decay_after_n_steps")
    if isinstance(decay_every, int) and decay_every <= 0:
        add(findings, "ERROR", "model.training_args.lr_decay_every_n_steps", "decay interval must be positive")

    if profile == "debug":
        if isinstance(data.get("max_tokens"), int) and data["max_tokens"] > 384:
            add(findings, "WARN", "data.max_tokens", "debug profile should usually lower max_tokens to 256 or 384")
        if isinstance(data.get("max_atoms"), int) and data["max_atoms"] > 3456:
            add(findings, "WARN", "data.max_atoms", "debug profile should usually lower max_atoms to 2304 or 3456")
        if isinstance(data.get("samples_per_epoch"), int) and data["samples_per_epoch"] > 1000:
            add(findings, "WARN", "data.samples_per_epoch", "debug smoke tests should use a small samples_per_epoch override")
        if trainer.get("max_epochs", None) in (-1, None):
            add(findings, "WARN", "trainer.max_epochs", "debug smoke tests should set a bounded max_epochs override")
        if data.get("num_workers", 0) != 0:
            add(findings, "INFO", "data.num_workers", "training debug=1 overrides this to 0")


def device_count(devices: Any) -> int | None:
    if isinstance(devices, int) and not isinstance(devices, bool):
        return devices
    if isinstance(devices, list):
        return len(devices)
    return None


def check_training_intent(config: dict[str, Any], profile: str, findings: list[Finding]) -> None:
    trainer = as_mapping(config.get("trainer"))
    devices = device_count(trainer.get("devices", 1))
    if profile == "debug":
        if devices is not None and devices > 1:
            add(findings, "INFO", "trainer.devices", "training debug=1 overrides multi-device settings to one device")
    elif devices is not None and devices > 1 and not config.get("find_unused_parameters", False):
        add(findings, "INFO", "find_unused_parameters", "multi-device runs use DDP; enable only if DDP reports unused parameters")

    resume = config.get("resume")
    pretrained = config.get("pretrained")
    if not is_empty(resume) and not is_empty(pretrained):
        add(findings, "WARN", "resume/pretrained", "resume wins; pretrained is ignored when resume is set")
    if config.get("validation_only") and is_empty(resume):
        add(findings, "ERROR", "validation_only", "validation_only requires resume to point at a checkpoint")
    if config.get("load_confidence_from_trunk") and not is_empty(resume):
        add(findings, "WARN", "load_confidence_from_trunk", "resume is set, so pretrained trunk loading path is skipped")
    if config.get("load_confidence_from_trunk") and is_empty(pretrained):
        add(findings, "ERROR", "load_confidence_from_trunk", "requires pretrained structure checkpoint when true")

    wandb = config.get("wandb")
    if isinstance(wandb, dict):
        for key in ("name", "project", "entity"):
            if not wandb.get(key):
                add(findings, "WARN", f"wandb.{key}", "wandb block is present but field is empty")
        if profile == "debug":
            add(findings, "INFO", "wandb", "training debug=1 disables wandb logging")


def check_imports(config: dict[str, Any], findings: list[Finding]) -> None:
    targets = collect_targets(config)
    if not targets:
        add(findings, "WARN", "_target_", "no Hydra targets found")
        return
    for path, target in targets:
        ok, reason = import_target(target)
        if not ok:
            add(findings, "ERROR", path, f"cannot import {target}: {reason}")


def print_findings(findings: list[Finding]) -> None:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for finding in sorted(findings, key=lambda item: (order.get(item.level, 9), item.path, item.message)):
        print(f"[{finding.level}] {finding.path}: {finding.message}")


def print_summary(config: dict[str, Any], profile: str) -> None:
    data = as_mapping(config.get("data"))
    trainer = as_mapping(config.get("trainer"))
    devices = trainer.get("devices", 1)
    max_tokens = data.get("max_tokens", "?")
    max_atoms = data.get("max_atoms", "?")
    num_workers = data.get("num_workers", "?")
    print("\nSummary:")
    print(f"- profile: {profile}")
    print(f"- trainer.devices: {devices}")
    print(f"- data.max_tokens/max_atoms: {max_tokens}/{max_atoms}")
    print(f"- data.num_workers: {num_workers}")
    if profile == "debug":
        print("\nSuggested debug override:")
        print(
            "Use these overrides with the official Boltz training launcher in "
            "the user's training checkout: debug=1 data.max_tokens=256 "
            "data.max_atoms=2304 data.samples_per_epoch=8 "
            "trainer.max_epochs=1 disable_checkpoint=true"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Boltz Hydra training config before debug or full training."
    )
    parser.add_argument("config", type=Path, help="Path to a Boltz training YAML config")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional root for resolving relative split paths referenced by the config", 
    )
    parser.add_argument(
        "--profile",
        choices=("debug", "full", "validation"),
        default="full",
        help="Validation lens to apply",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Import every Hydra _target_; requires a working Boltz training environment",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Exit nonzero when warnings are present",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = args.config.expanduser().resolve()
    if not config_path.exists():
        print(f"Config file does not exist: {config_path}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"Config path is not a file: {config_path}", file=sys.stderr)
        return 2

    config = load_yaml(config_path)
    findings: list[Finding] = []
    check_top_level(config, findings)
    if isinstance(config, dict):
        base_dir = args.repo_root.expanduser().resolve() if args.repo_root else config_path.parent
        walk_placeholders(config, "", findings)
        check_paths(config, base_dir, findings)
        check_datasets(config, base_dir, findings)
        check_numeric(config, args.profile, findings)
        check_training_intent(config, args.profile, findings)
        if args.profile == "validation" and not config.get("validation_only"):
            add(findings, "WARN", "validation_only", "validation profile was requested but validation_only is not true")
        if args.check_imports:
            check_imports(config, findings)

    print_findings(findings)
    if isinstance(config, dict):
        print_summary(config, args.profile)

    errors = sum(1 for finding in findings if finding.level == "ERROR")
    warnings = sum(1 for finding in findings if finding.level == "WARN")
    infos = sum(1 for finding in findings if finding.level == "INFO")
    print(f"\nResult: {errors} error(s), {warnings} warning(s), {infos} info item(s).")
    if errors or (warnings and args.warnings_as_errors):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

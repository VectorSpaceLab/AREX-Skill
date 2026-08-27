#!/usr/bin/env python3
"""Safe MimicKit runner/layout checker.

This script validates the expected runner, builder, engine-config, and preset
layout without importing simulator backends.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

EXTERNAL_ALLOWED_PREFIXES = (
    "data/motions/",
    "data/models/",
    "data/logs/",
    "data/assets/objects/",
)

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "mimickit/run.py",
    "mimickit/util/arg_parser.py",
    "mimickit/envs/env_builder.py",
    "mimickit/learning/agent_builder.py",
    "mimickit/engines/engine_builder.py",
    "data/engines/isaac_gym_engine.yaml",
    "data/engines/isaac_lab_engine.yaml",
    "data/engines/newton_engine.yaml",
]

REQUIRED_DIRS = [
    "args",
    "data/engines",
    "data/envs",
    "data/agents",
    "data/datasets",
    "data/assets/humanoid",
    "mimickit/envs",
    "mimickit/learning",
    "mimickit/engines",
    "mimickit/util",
]

ENGINE_NAME_BY_FILE = {
    "isaac_gym_engine.yaml": "isaac_gym",
    "isaac_lab_engine.yaml": "isaac_lab",
    "newton_engine.yaml": "newton",
}

KEYS_WITH_PATHS = {
    "engine_config",
    "env_config",
    "agent_config",
    "model_file",
    "motion_file",
    "dataset_file",
    "char_file",
}

BOOL_LITERALS = {"true", "false", "True", "False", "1", "0", "t", "T", "f", "F"}


def tokenize_args_file(path: Path) -> List[str]:
    tokens: List[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        for token in raw_line.split():
            if token.startswith("#"):
                break
            tokens.append(token)
    return tokens


def parse_token_stream(tokens: Iterable[str]) -> Dict[str, List[str]]:
    table: Dict[str, List[str]] = {}
    curr_key = ""
    vals: List[str] = []

    def commit() -> None:
        nonlocal curr_key, vals
        if curr_key and curr_key not in table:
            table[curr_key] = list(vals)

    for token in tokens:
        if token.startswith("--") and len(token) >= 3:
            if curr_key:
                commit()
            curr_key = token[2:]
            vals = []
        else:
            vals.append(token)

    if curr_key:
        commit()
    return table


def first_value(table: Dict[str, List[str]], key: str, default: str = "") -> str:
    values = table.get(key)
    if not values:
        return default
    return values[0]


def is_bool_literal(value: str) -> bool:
    return value in BOOL_LITERALS


def is_external_path(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in EXTERNAL_ALLOWED_PREFIXES)


def check_repo_root(repo_root: Path) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    for rel in REQUIRED_FILES:
        abs_path = repo_root / rel
        if not abs_path.is_file():
            errors.append(f"missing required file: {rel}")

    for rel in REQUIRED_DIRS:
        abs_path = repo_root / rel
        if not abs_path.is_dir():
            errors.append(f"missing required directory: {rel}")

    args_dir = repo_root / "args"
    if args_dir.is_dir():
        preset_files = sorted(args_dir.glob("*.txt"))
        if not preset_files:
            warnings.append("no preset files found under args/")
        for preset_path in preset_files:
            rel = preset_path.relative_to(repo_root).as_posix()
            tokens = tokenize_args_file(preset_path)
            table = parse_token_stream(tokens)

            mode = first_value(table, "mode", "train")
            if mode not in {"train", "test"}:
                errors.append(f"{rel}: unsupported mode value {mode!r}")

            num_envs = first_value(table, "num_envs", "")
            if num_envs:
                try:
                    if int(num_envs) < 1:
                        errors.append(f"{rel}: num_envs must be positive")
                except ValueError:
                    errors.append(f"{rel}: num_envs is not an integer: {num_envs!r}")

            for key in KEYS_WITH_PATHS:
                raw_value = first_value(table, key, "")
                if not raw_value:
                    continue
                rel_value = raw_value
                abs_value = repo_root / rel_value
                if abs_value.exists():
                    continue
                if is_external_path(rel_value):
                    warnings.append(f"{rel}: external asset missing but allowed for checkout-local layout checks: {rel_value}")
                else:
                    errors.append(f"{rel}: referenced path does not exist: {rel_value}")

            for bool_key in ("visualize", "video", "save_int_models"):
                raw_value = first_value(table, bool_key, "")
                if raw_value and not is_bool_literal(raw_value):
                    errors.append(f"{rel}: {bool_key} is not a supported boolean literal: {raw_value!r}")

            devices = table.get("devices", [])
            if devices and any(token.startswith("--") for token in devices):
                errors.append(f"{rel}: malformed devices value")

            model_file = first_value(table, "model_file", "")
            if model_file and not (repo_root / model_file).exists():
                if is_external_path(model_file):
                    warnings.append(f"{rel}: external model missing but allowed for layout checks: {model_file}")
                else:
                    warnings.append(f"{rel}: model_file does not exist in checkout: {model_file}")

    return errors, warnings, info


def check_engine_configs(repo_root: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    engine_dir = repo_root / "data" / "engines"
    for filename, expected_engine in ENGINE_NAME_BY_FILE.items():
        path = engine_dir / filename
        if not path.is_file():
            continue
        found_engine = None
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("engine_name:"):
                found_engine = line.split(":", 1)[1].strip().strip('"\'')
                break
        if found_engine is None:
            errors.append(f"{path.relative_to(repo_root).as_posix()}: missing engine_name")
        elif found_engine != expected_engine:
            errors.append(
                f"{path.relative_to(repo_root).as_posix()}: engine_name={found_engine!r} does not match expected {expected_engine!r}"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the MimicKit runner/backend layout without importing simulator backends.")
    parser.add_argument("--repo-root", required=True, help="Path to a MimicKit checkout root.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary in addition to the human summary.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    errors: List[str] = []
    warnings: List[str] = []

    if not repo_root.exists():
        errors.append(f"repo root does not exist: {repo_root}")
    elif not repo_root.is_dir():
        errors.append(f"repo root is not a directory: {repo_root}")
    else:
        layout_errors, layout_warnings, _ = check_repo_root(repo_root)
        errors.extend(layout_errors)
        warnings.extend(layout_warnings)

        engine_errors, engine_warnings = check_engine_configs(repo_root)
        errors.extend(engine_errors)
        warnings.extend(engine_warnings)

    summary = {
        "repo_root": str(repo_root),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }

    print("MimicKit layout check")
    print(f"repo_root: {repo_root}")
    print(f"status: {'OK' if not errors else 'FAIL'}")
    print(f"errors: {len(errors)}")
    print(f"warnings: {len(warnings)}")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("\nErrors:")
        for item in errors:
            print(f"- {item}")

    if args.json:
        print("\nJSON:")
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

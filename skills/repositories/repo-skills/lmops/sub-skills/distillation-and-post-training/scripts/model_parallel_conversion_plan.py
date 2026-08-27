#!/usr/bin/env python3
"""Plan MiniLLM/DPKD tensor-parallel checkpoint conversion without writing files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence

MINILLM_TYPES = {"opt", "qwen2", "llama", "mistral"}
DPKD_TYPES = {"opt", "gptj", "llama", "llama2", "mistral", "qwen"}
ALIASES = {
    "qwen2.5": "qwen2",
    "llama-2": "llama2",
}
WEIGHT_MARKERS = (
    "pytorch_model.bin",
    "model.safetensors",
    "pytorch_model-*.bin",
    "model-*.safetensors",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MiniLLM/DPKD model type, source/target MP sizes, and "
            "checkpoint path layout. The script prints a plan only; it never "
            "loads or writes model tensors."
        )
    )
    parser.add_argument("--input-path", required=True, help="Local checkpoint root to inspect.")
    parser.add_argument("--model-type", required=True, help="Model family name, e.g. llama or opt.")
    parser.add_argument("--source-mp-size", required=True, type=int, help="Current tensor-parallel shard count.")
    parser.add_argument("--target-mp-size", required=True, type=int, help="Desired tensor-parallel shard count.")
    parser.add_argument(
        "--project",
        choices=["auto", "minillm", "dpkd"],
        default="auto",
        help="Restrict model-type validation to a project-specific converter.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help=(
            "Optional planned final output path. For split/rechunk this is a "
            "shard directory; for merge it may be a directory or a .bin file."
        ),
    )
    parser.add_argument(
        "--dtype",
        choices=["torch.float32", "torch.float16", "torch.bfloat16"],
        default="torch.float16",
        help="Planned dtype argument for converters that expose it.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow existing destination files in the printed plan.",
    )
    return parser.parse_args()


def normalize_model_type(value: str) -> str:
    value = value.strip().lower()
    return ALIASES.get(value, value)


def supported_projects(model_type: str) -> List[str]:
    projects: List[str] = []
    if model_type in MINILLM_TYPES:
        projects.append("minillm")
    if model_type in DPKD_TYPES:
        projects.append("dpkd")
    return projects


def infer_operation(source: int, target: int) -> str:
    if source == target:
        return "no-op"
    if source == 1 and target > 1:
        return "split_from_monolith"
    if source > 1 and target == 1:
        return "merge_to_monolith"
    if source > 1 and target > 1:
        return "merge_then_split"
    return "invalid"


def has_weight_marker(root: Path) -> bool:
    for pattern in WEIGHT_MARKERS:
        if list(root.glob(pattern)):
            return True
    return False


def expected_output(args: argparse.Namespace, operation: str) -> Dict[str, str]:
    root = Path(args.input_path)
    if operation in {"split_from_monolith", "merge_then_split"}:
        output_dir = Path(args.output_path) if args.output_path else root / f"mp{args.target_mp_size}"
        return {"kind": "shard_directory", "path": str(output_dir)}

    if operation == "merge_to_monolith":
        if args.output_path:
            proposed = Path(args.output_path)
            if proposed.suffix == ".bin":
                output_file = proposed
            else:
                output_file = proposed / "pytorch_model.bin"
        else:
            output_file = root / "pytorch_model.bin"
        return {"kind": "monolithic_file", "path": str(output_file)}

    return {"kind": "unknown", "path": args.output_path or ""}


def validate_model_type(project: str, model_type: str) -> List[str]:
    errors: List[str] = []
    projects = supported_projects(model_type)
    if not projects:
        errors.append(
            f"unsupported model type {model_type!r}; MiniLLM supports {sorted(MINILLM_TYPES)}, "
            f"DPKD supports {sorted(DPKD_TYPES)}"
        )
    elif project != "auto" and project not in projects:
        errors.append(
            f"model type {model_type!r} is not supported by the {project} converter; "
            f"supported projects for it: {projects}"
        )
    return errors


def validate_sizes(source: int, target: int) -> List[str]:
    errors: List[str] = []
    if source <= 0:
        errors.append("source MP size must be a positive integer")
    if target <= 0:
        errors.append("target MP size must be a positive integer")
    if source == target:
        errors.append("source and target MP sizes are equal; no conversion would be planned")
    return errors


def validate_paths(args: argparse.Namespace, operation: str) -> tuple[List[str], List[str], List[str]]:
    checks: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []
    root = Path(args.input_path)

    if not root.exists():
        errors.append(f"input path does not exist: {args.input_path}")
        return checks, warnings, errors
    if not root.is_dir():
        errors.append(f"input path is not a directory: {args.input_path}")
        return checks, warnings, errors

    checks.append("input path exists and is a directory")

    config_path = root / "config.json"
    if config_path.exists():
        checks.append("checkpoint root contains config.json")
    else:
        errors.append("checkpoint root is missing config.json")

    if operation == "split_from_monolith":
        if has_weight_marker(root):
            checks.append("monolithic checkpoint weight marker found")
        else:
            errors.append("source MP size is 1 but no monolithic weight marker was found")

    if operation in {"merge_to_monolith", "merge_then_split"}:
        shard_dir = root / f"mp{args.source_mp_size}"
        if not shard_dir.exists() or not shard_dir.is_dir():
            errors.append(f"source MP shard directory is missing: {shard_dir}")
        else:
            checks.append(f"source shard directory exists: {shard_dir}")
            missing = [
                str(shard_dir / f"pytorch_model_{idx}.bin")
                for idx in range(args.source_mp_size)
                if not (shard_dir / f"pytorch_model_{idx}.bin").exists()
            ]
            if missing:
                errors.append("missing expected source shard files: " + ", ".join(missing))
            else:
                checks.append("all expected source shard files are present")

    output = expected_output(args, operation)
    output_path = Path(output["path"]) if output["path"] else None
    if output_path:
        if output["kind"] == "shard_directory":
            if output_path.exists() and output_path.is_file():
                errors.append(f"planned shard output path is an existing file: {output_path}")
            collisions = [
                str(output_path / f"pytorch_model_{idx}.bin")
                for idx in range(args.target_mp_size)
                if (output_path / f"pytorch_model_{idx}.bin").exists()
            ]
            if collisions and not args.allow_existing:
                errors.append("planned output shard files already exist: " + ", ".join(collisions))
            elif collisions:
                warnings.append("planned output shard files already exist and --allow-existing was set")
            else:
                checks.append("no planned output shard-file collision detected")
        elif output["kind"] == "monolithic_file":
            if output_path.exists() and not args.allow_existing:
                errors.append(f"planned output file already exists: {output_path}")
            elif output_path.exists():
                warnings.append("planned output file already exists and --allow-existing was set")
            else:
                checks.append("no planned monolithic output-file collision detected")

    return checks, warnings, errors


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    normalized_model_type = normalize_model_type(args.model_type)
    operation = infer_operation(args.source_mp_size, args.target_mp_size)

    errors: List[str] = []
    warnings: List[str] = []
    checks: List[str] = []

    errors.extend(validate_sizes(args.source_mp_size, args.target_mp_size))
    errors.extend(validate_model_type(args.project, normalized_model_type))

    if operation in {"split_from_monolith", "merge_to_monolith", "merge_then_split"}:
        path_checks, path_warnings, path_errors = validate_paths(args, operation)
        checks.extend(path_checks)
        warnings.extend(path_warnings)
        errors.extend(path_errors)
    else:
        errors.append(f"invalid conversion operation for source={args.source_mp_size}, target={args.target_mp_size}")

    output = expected_output(args, operation)
    root = Path(args.input_path)
    source_layout = "monolithic" if args.source_mp_size == 1 else str(root / f"mp{args.source_mp_size}")

    notes: List[str] = [
        "This script does not load, merge, split, or write checkpoint tensors.",
        "It validates only model-type support, integer MP sizes, and filesystem layout.",
    ]
    if operation == "merge_then_split":
        notes.append("The real converter materializes a monolithic intermediate before writing target shards.")
    if normalized_model_type != args.model_type.strip().lower():
        notes.append(f"Normalized model type {args.model_type!r} to {normalized_model_type!r}.")

    return {
        "status": "error" if errors else "ok",
        "project_request": args.project,
        "supported_projects": supported_projects(normalized_model_type),
        "model_type": normalized_model_type,
        "source_mp_size": args.source_mp_size,
        "target_mp_size": args.target_mp_size,
        "operation": operation,
        "input_path": args.input_path,
        "source_layout": source_layout,
        "planned_output": output,
        "dtype": args.dtype,
        "allow_existing": bool(args.allow_existing),
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "notes": notes,
    }


def main() -> int:
    args = parse_args()
    plan = build_plan(args)
    json.dump(plan, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if plan["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

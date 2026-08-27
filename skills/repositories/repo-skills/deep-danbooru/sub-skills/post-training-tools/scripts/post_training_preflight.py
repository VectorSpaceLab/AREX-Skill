#!/usr/bin/env python3
"""Deterministic, side-effect-free preflight for post-training paths.

This checker deliberately does not import TensorFlow or DeepDanbooru. It only
inspects local paths and project JSON, so it is safe to run before an expensive
conversion or image-writing workflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check DeepDanbooru post-training paths and optimization selection "
            "without loading a model or using the network."
        )
    )
    parser.add_argument("--project-path", type=Path, help="Project directory.")
    parser.add_argument("--model-path", type=Path, help="Saved Keras model file.")
    parser.add_argument("--save-path", type=Path, help="Output .tflite file.")
    parser.add_argument(
        "--optimize-default", action="store_true", help="Select default optimization."
    )
    parser.add_argument(
        "--optimize-experimental-sparsity",
        action="store_true",
        help="Select experimental sparsity optimization.",
    )
    parser.add_argument(
        "--allow-existing-output",
        action="store_true",
        help="Allow replacing an existing regular output file; directories always fail.",
    )
    return parser.parse_args(argv)


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def project_model_path(project: Path) -> tuple[Path | None, list[str]]:
    notes: list[str] = []
    context_path = project / "project.json"
    if not context_path.is_file():
        error(f"project metadata is missing: {context_path}")
        return None, notes
    try:
        context: Any = json.loads(context_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error(f"cannot read project.json: {exc}")
        return None, notes
    model_name = context.get("model") if isinstance(context, dict) else None
    if not isinstance(model_name, str) or not model_name.strip():
        error('project.json must contain a non-empty string "model" value')
        return None, notes
    candidates = [project / f"model-{model_name}.keras", project / f"model-{model_name}.h5"]
    for candidate in candidates:
        if candidate.is_file():
            notes.append(f"project model: {candidate.name}")
            return candidate, notes
    error("project model not found; tried " + ", ".join(p.name for p in candidates))
    return None, notes


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures = 0
    notes: list[str] = []

    if args.project_path is None and args.model_path is None:
        error("provide one of --project-path or --model-path")
        failures += 1

    if args.save_path is None:
        error("--save-path is required")
        failures += 1
    elif args.save_path.exists() and args.save_path.is_dir():
        error(f"save path is a directory: {args.save_path}")
        failures += 1
    elif args.save_path.exists() and not args.allow_existing_output:
        print(f"WARNING: output already exists and may be overwritten: {args.save_path}")
    elif args.save_path.suffix.lower() != ".tflite":
        print("WARNING: save path does not use the expected .tflite suffix")

    if not (args.optimize_default or args.optimize_experimental_sparsity):
        error("select at least one optimization")
        failures += 1

    if args.project_path is not None:
        if not args.project_path.is_dir():
            error(f"project path is not a directory: {args.project_path}")
            failures += 1
        elif args.model_path is None:
            model, project_notes = project_model_path(args.project_path)
            notes.extend(project_notes)
            if model is None:
                failures += 1
            tags_path = args.project_path / "tags.txt"
            if not tags_path.is_file():
                print(f"WARNING: project tags file is missing: {tags_path}")
        else:
            notes.append("project contents not inspected: direct model takes precedence")

    if args.model_path is not None:
        if not args.model_path.is_file():
            error(f"model path is not a file: {args.model_path}")
            failures += 1
        else:
            notes.append(f"direct model: {args.model_path.name}")

    if args.save_path is not None:
        parent = args.save_path.parent
        if not parent.exists():
            print(f"WARNING: save parent does not exist and must be created: {parent}")
        elif not parent.is_dir():
            error(f"save parent is not a directory: {parent}")
            failures += 1

    if failures:
        print(f"Preflight failed with {failures} error(s).", file=sys.stderr)
        return 2

    selected = []
    if args.optimize_default:
        selected.append("DEFAULT")
    if args.optimize_experimental_sparsity:
        selected.append("EXPERIMENTAL_SPARSITY")
    print("Preflight OK")
    print("Selected optimizations: " + ", ".join(selected))
    for note in notes:
        print(note)
    print("No model was loaded; no files were created; no network was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

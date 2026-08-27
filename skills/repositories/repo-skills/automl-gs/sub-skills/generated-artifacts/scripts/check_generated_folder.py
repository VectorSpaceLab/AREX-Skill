#!/usr/bin/env python3
"""Validate a generated automl-gs artifact folder.

This helper is self-contained: it inspects only the generated folder passed as
a command-line argument and does not import the original repository checkout.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable

CORE_FILES = ["model.py", "pipeline.py", "requirements.txt"]
CORE_DIRS = ["encoders", "metadata"]
EXPECTED_FLAGS = [
    "-d/--data",
    "-m/--mode",
    "-s/--split",
    "-e/--epochs",
    "-c/--context",
    "-t/--type",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def detect_framework(folder: Path) -> str:
    requirements = read_text(folder / "requirements.txt").lower()
    model_text = read_text(folder / "model.py").lower()
    pipeline_text = read_text(folder / "pipeline.py").lower()

    if (
        "xgboost" in requirements
        or "xgb.booster" in model_text
        or "model.bin" in model_text
        or "xgb.train" in pipeline_text
    ):
        return "xgboost"

    if (
        "tensorflow" in requirements
        or "load_weights" in model_text
        or "model_weights.hdf5" in model_text
        or "keras" in pipeline_text
    ):
        return "tensorflow"

    return "unknown"


def list_json_files(folder: Path) -> list[str]:
    if not folder.is_dir():
        return []
    return sorted(path.name for path in folder.glob("*.json"))


def pick_model_file(framework: str) -> str:
    if framework == "tensorflow":
        return "model_weights.hdf5"
    return "model.bin"


def describe_expected_outputs(framework: str) -> list[str]:
    model_file = pick_model_file(framework)
    return [
        "metadata/results.csv",
        model_file,
        "predictions.csv",
        "predictions.json",
    ]


def missing(items: Iterable[str], folder: Path) -> list[str]:
    out: list[str] = []
    for item in items:
        path = folder / item
        if not path.exists():
            out.append(item)
    return out


def emit_report(folder: Path, framework: str) -> None:
    print(f"Generated folder: {folder.resolve()}")
    print(f"Detected framework: {framework}")
    print("Expected modes: train, predict")
    print(f"Expected CLI flags: {', '.join(EXPECTED_FLAGS)}")
    print("Core files: model.py, pipeline.py, requirements.txt")
    print("Core directories: encoders/, metadata/")
    print(f"Expected train artifacts: metadata/results.csv, {pick_model_file(framework)}")
    print("Expected predict outputs: predictions.csv or predictions.json")

    encoders = list_json_files(folder / "encoders")
    metadata = folder / "metadata" / "results.csv"

    if encoders:
        print("Encoder JSON files:")
        for name in encoders:
            print(f"  - {name}")
    else:
        print("Encoder JSON files: none found yet")

    model_file = pick_model_file(framework)
    if metadata.exists():
        print("metadata/results.csv: present")
    else:
        print("metadata/results.csv: missing")

    if (folder / model_file).exists():
        print(f"{model_file}: present")
    else:
        print(f"{model_file}: missing")

    for candidate in ("predictions.csv", "predictions.json"):
        if (folder / candidate).exists():
            print(f"{candidate}: present")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the structure of a generated automl-gs artifact folder "
            "and print the expected runtime files."
        )
    )
    parser.add_argument("folder", help="Path to the generated artifact folder")
    parser.add_argument(
        "--framework",
        choices=("auto", "xgboost", "tensorflow"),
        default="auto",
        help="Override framework detection when the folder is ambiguous.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when core files or the detected framework are missing.",
    )
    parser.add_argument(
        "--expect-trained",
        action="store_true",
        help="Require the framework model file and metadata/results.csv.",
    )
    parser.add_argument(
        "--expect-predictions",
        action="store_true",
        help="Require at least one predictions file in the folder.",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"error: folder does not exist: {folder}", file=sys.stderr)
        return 1
    if not folder.is_dir():
        print(f"error: not a directory: {folder}", file=sys.stderr)
        return 1

    detected = detect_framework(folder)
    framework = detected if args.framework == "auto" else args.framework
    emit_report(folder, framework)

    core_missing = missing(CORE_FILES, folder) + [name for name in CORE_DIRS if not (folder / name).is_dir()]
    if core_missing:
        print(f"core layout missing: {', '.join(core_missing)}", file=sys.stderr)
        if args.strict:
            return 1

    if args.framework == "auto" and detected == "unknown" and args.strict:
        print("core layout present but framework could not be detected", file=sys.stderr)
        return 1

    if args.expect_trained:
        trained_missing = missing([pick_model_file(framework), "metadata/results.csv"], folder)
        if trained_missing:
            print(f"trained artifacts missing: {', '.join(trained_missing)}", file=sys.stderr)
            return 1

    if args.expect_predictions:
        if not any((folder / candidate).exists() for candidate in ("predictions.csv", "predictions.json")):
            print("predictions file missing: expected predictions.csv or predictions.json", file=sys.stderr)
            return 1

    print("Expected runtime files:")
    for item in describe_expected_outputs(framework):
        print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

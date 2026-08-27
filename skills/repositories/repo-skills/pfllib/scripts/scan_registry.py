#!/usr/bin/env python3
"""Scan the PFLlib algorithm, model, and dataset registries.

This helper reads the checkout source tree without importing the full training
stack. It is useful before extending the repo or when you need a quick snapshot
of the supported launch surface.

Examples:
  python scan_registry.py --repo-root /path/to/PFLlib
  python scan_registry.py --repo-root /path/to/PFLlib --format json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def extract_branches(text: str, pattern: str) -> list[str]:
    return unique_ordered(re.findall(pattern, text))


def build_snapshot(repo_root: Path) -> dict:
    system_dir = repo_root / "system"
    dataset_dir = repo_root / "dataset"
    main_py = system_dir / "main.py"
    models_py = system_dir / "flcore" / "trainmodel" / "models.py"

    if not main_py.is_file():
        raise FileNotFoundError(f"missing main.py at {main_py}")
    if not models_py.is_file():
        raise FileNotFoundError(f"missing models.py at {models_py}")
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"missing dataset/ at {dataset_dir}")

    main_text = main_py.read_text()
    model_text = models_py.read_text()

    algorithms = extract_branches(main_text, r"args\.algorithm\s*==\s*[\"']([^\"']+)[\"']")
    models = extract_branches(main_text, r"model_str\s*==\s*[\"']([^\"']+)[\"']")
    generators = sorted(p.name for p in dataset_dir.glob("generate_*.py"))

    dependency_hints = {
        "cvxpy": ["FedPAC"],
        "torchtext": ["AGNews", "SogouNews", "LSTM", "BiLSTM", "fastText", "TextCNN", "Transformer"],
        "torchvision": ["ResNet18", "ResNet34", "AlexNet", "GoogleNet", "MobileNet"],
    }

    source_files = {
        "main": str(main_py.relative_to(repo_root)),
        "models": str(models_py.relative_to(repo_root)),
        "generators": [str(path.relative_to(repo_root)) for path in sorted(dataset_dir.glob("generate_*.py"))],
    }

    return {
        "repository": repo_root.name,
        "algorithms": algorithms,
        "models": models,
        "generators": generators,
        "dependency_hints": dependency_hints,
        "source_files": source_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Path to the PFLlib checkout.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    snapshot = build_snapshot(repo_root)

    if args.format == "json":
        print(json.dumps(snapshot, indent=2))
        return 0

    print(f"repository: {snapshot['repository']}")
    print(f"algorithms ({len(snapshot['algorithms'])}):")
    for item in snapshot["algorithms"]:
        print(f"  - {item}")
    print(f"models ({len(snapshot['models'])}):")
    for item in snapshot["models"]:
        print(f"  - {item}")
    print(f"dataset_generators ({len(snapshot['generators'])}):")
    for item in snapshot["generators"]:
        print(f"  - {item}")
    print("dependency_hints:")
    for name, items in snapshot["dependency_hints"].items():
        print(f"  {name}: {', '.join(items)}")
    print("source_files:")
    print(f"  main: {snapshot['source_files']['main']}")
    print(f"  models: {snapshot['source_files']['models']}")
    for item in snapshot["source_files"]["generators"]:
        print(f"  generator: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

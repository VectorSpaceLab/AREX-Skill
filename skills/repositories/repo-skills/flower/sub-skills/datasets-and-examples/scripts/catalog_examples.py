#!/usr/bin/env python3
"""Catalog Flower example projects and their dependency/wiring patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

EXTRA_PATTERNS = {
    "vision-extra": re.compile(r"flwr-datasets\[vision\]", re.IGNORECASE),
    "audio-extra": re.compile(r"flwr-datasets\[audio\]", re.IGNORECASE),
}

DEPENDENCY_PATTERNS = {
    "simulation": re.compile(r"flwr\[simulation\]", re.IGNORECASE),
    "torch": re.compile(
        r"\b(torch|torchvision|fastai|pytorch-lightning|opacus)\b",
        re.IGNORECASE,
    ),
    "tensorflow": re.compile(r"tensorflow", re.IGNORECASE),
    "mlx": re.compile(r"\bmlx\b", re.IGNORECASE),
    "jax": re.compile(r"\b(jax|jaxlib|flax)\b", re.IGNORECASE),
    "tabular": re.compile(r"\b(pandas|scikit-learn|catboost|xgboost)\b", re.IGNORECASE),
    "llm": re.compile(
        r"\b(transformers|trl|peft|bitsandbytes|sentencepiece|fschat)\b",
        re.IGNORECASE,
    ),
    "rag": re.compile(r"\b(faiss-cpu|sentence_transformers)\b", re.IGNORECASE),
    "security": re.compile(r"\b(cryptography|opacus)\b", re.IGNORECASE),
    "quantum": re.compile(r"pennylane", re.IGNORECASE),
    "medical": re.compile(r"monai", re.IGNORECASE),
    "robotics": re.compile(r"lerobot", re.IGNORECASE),
    "network-heavy": re.compile(r"git\+https|hf_transfer", re.IGNORECASE),
}


def _flatten_keys(value: Any, prefix: str = "") -> list[str]:
    """Flatten nested mapping keys to dot-separated strings."""
    if not isinstance(value, dict):
        return []
    flattened: list[str] = []
    for key, nested in value.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(nested, dict):
            flattened.extend(_flatten_keys(nested, full_key))
        else:
            flattened.append(full_key)
    return flattened


def _extract_component_modules(components: dict[str, Any]) -> dict[str, str]:
    """Return only module paths from `module:object` component references."""
    module_paths: dict[str, str] = {}
    for component_name, reference in components.items():
        if isinstance(reference, str) and ":" in reference:
            module_paths[component_name] = reference.split(":", 1)[0]
    return module_paths


def _classify_dependencies(dependencies: Iterable[str]) -> list[str]:
    """Attach lightweight tags to a dependency list."""
    deps = [str(dep) for dep in dependencies]
    joined = "\n".join(deps)
    tags: set[str] = set()
    for tag, pattern in EXTRA_PATTERNS.items():
        if pattern.search(joined):
            tags.add(tag)
    for tag, pattern in DEPENDENCY_PATTERNS.items():
        if pattern.search(joined):
            tags.add(tag)
    if any("flwr-datasets" in dep.lower() for dep in deps):
        tags.add("datasets")
    return sorted(tags)


def _read_example_record(pyproject_path: Path, root: Path) -> dict[str, Any] | None:
    """Read one example `pyproject.toml` file."""
    data = tomllib.loads(pyproject_path.read_text())
    tool_flwr = data.get("tool", {}).get("flwr", {}).get("app", {})
    components = tool_flwr.get("components", {})
    if not isinstance(components, dict) or not components:
        return None

    project = data.get("project", {})
    dependencies = project.get("dependencies", [])
    if not isinstance(dependencies, list):
        dependencies = []

    record = {
        "project_dir": str(pyproject_path.parent.relative_to(root)),
        "project_name": project.get("name"),
        "components": components,
        "component_modules": _extract_component_modules(components),
        "dependency_tags": _classify_dependencies(str(dep) for dep in dependencies),
        "dependencies": [str(dep) for dep in dependencies],
        "publisher": tool_flwr.get("publisher"),
        "fab_format_version": tool_flwr.get("fab-format-version"),
        "flwr_version_target": tool_flwr.get("flwr-version-target"),
        "fab_include": tool_flwr.get("fab-include"),
        "config_keys": sorted(_flatten_keys(tool_flwr.get("config", {}))),
    }
    return record


def _discover_pyprojects(root: Path) -> list[Path]:
    """Find example `pyproject.toml` files under the given root."""
    return sorted(path for path in root.glob("**/pyproject.toml") if path.is_file())


def _resolve_root(raw_root: str | None) -> Path:
    """Resolve the example root directory."""
    if raw_root is not None:
        candidate = Path(raw_root).expanduser().resolve()
        if candidate.name == "examples" and candidate.is_dir():
            return candidate
        if (candidate / "examples").is_dir():
            return (candidate / "examples").resolve()
        return candidate

    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "examples").is_dir():
            return (candidate / "examples").resolve()
        if candidate.name == "examples" and candidate.is_dir():
            return candidate
    raise SystemExit("Could not locate an `examples/` directory. Pass --root explicitly.")


def _print_markdown(records: list[dict[str, Any]]) -> None:
    """Render a compact markdown table."""
    print("| Project dir | Project name | Components | Tags | Config keys |")
    print("| --- | --- | --- | --- | --- |")
    for record in records:
        components = ", ".join(
            f"{name}={reference}" for name, reference in record["components"].items()
        )
        tags = ", ".join(record["dependency_tags"]) or "-"
        config_keys = ", ".join(record["config_keys"]) or "-"
        print(
            f"| {record['project_dir']} | {record['project_name']} | {components} | {tags} | {config_keys} |"
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Print a read-only catalog of Flower example projects."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        help="Path to the examples directory or repository root.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args(argv)

    root = _resolve_root(args.root)
    pyprojects = _discover_pyprojects(root)
    records = []
    for pyproject_path in pyprojects:
        record = _read_example_record(pyproject_path, root)
        if record is not None:
            records.append(record)

    if args.format == "json":
        json.dump(records, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"# Flower example catalog ({len(records)} projects)")
        _print_markdown(records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

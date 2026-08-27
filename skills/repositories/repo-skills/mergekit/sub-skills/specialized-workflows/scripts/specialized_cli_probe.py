#!/usr/bin/env python3
"""Safe specialty preflight for installed mergekit entry points.

This script only parses local YAML or asks installed console commands for help.
It never imports mergekit, downloads models, opens checkpoints, runs a merge,
or writes outside stdout/stderr.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment-dependent
    yaml = None
    YAML_ERROR = str(exc)
else:
    YAML_ERROR = ""

COMMANDS = (
    "mergekit-pytorch",
    "mergekit-multi",
    "mergekit-moe",
    "mergekit-extract-lora",
    "mergekit-tokensurgeon",
    "mergekit-layershuffle",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--help-check",
        action="store_true",
        help="run --help for each verified installed specialty command",
    )
    group.add_argument(
        "--check-multistage",
        metavar="CONFIG",
        help="parse local YAML documents and validate named dependencies",
    )
    return parser


def help_check() -> int:
    failures = 0
    for command in COMMANDS:
        executable = shutil.which(command)
        if executable is None:
            print(f"MISSING {command}: not found on PATH", file=sys.stderr)
            failures += 1
            continue
        result = subprocess.run(
            [executable, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            # No cwd, source path, model path, or credential changes.
            env=os.environ.copy(),
        )
        if result.returncode:
            print(f"FAIL {command}: exit {result.returncode}", file=sys.stderr)
            print(result.stdout.rstrip(), file=sys.stderr)
            failures += 1
        else:
            print(f"OK {command}: {executable}")
    return 1 if failures else 0


def _model_reference(value: Any) -> str | None:
    """Return a path from a mergekit model-reference value."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        model = value.get("path")
        if isinstance(model, str):
            return model
        # Accept a defensive nested form for hand-authored fixtures.
        nested = value.get("model")
        if isinstance(nested, str):
            return nested
        if isinstance(nested, dict) and isinstance(nested.get("path"), str):
            return nested["path"]
    return None


def _references(value: Any) -> Iterable[str]:
    """Yield only values in model/base_model fields, never YAML names."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"model", "base_model"}:
                reference = _model_reference(child)
                if reference is not None:
                    yield reference
            yield from _references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _references(child)


def check_multistage(filename: str) -> int:
    if yaml is None:
        print(f"FAIL YAML parser unavailable: {YAML_ERROR}", file=sys.stderr)
        return 1

    path = Path(filename)
    if not path.is_file():
        print(f"FAIL config does not exist or is not a file: {path}", file=sys.stderr)
        return 1

    try:
        with path.open("r", encoding="utf-8") as stream:
            documents = list(yaml.safe_load_all(stream))
    except Exception as exc:  # safe parser boundary
        print(f"FAIL YAML parse: {exc}", file=sys.stderr)
        return 1

    if not documents or any(not isinstance(doc, dict) for doc in documents):
        print("FAIL every YAML document must be a mapping", file=sys.stderr)
        return 1

    names: list[str] = []
    for index, document in enumerate(documents, 1):
        if "name" in document:
            name = document["name"]
            if not isinstance(name, str) or not name.strip():
                print(f"FAIL document {index}: name must be a non-empty string", file=sys.stderr)
                return 1
            names.append(name)

    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        print(f"FAIL duplicate merge name(s): {', '.join(duplicates)}", file=sys.stderr)
        return 1

    unnamed = sum("name" not in document for document in documents)
    if unnamed > 1:
        print("FAIL at most one unnamed final document is supported", file=sys.stderr)
        return 1

    declared = set(names)
    dependencies: dict[str, set[str]] = {}
    undeclared_bare: set[str] = set()
    for index, document in enumerate(documents, 1):
        owner = str(document.get("name", "<final>"))
        found: set[str] = set()
        for reference in _references(document):
            if reference in declared:
                found.add(reference)  # exact declared-name match only
            elif (
                isinstance(reference, str)
                and reference
                and not any(mark in reference for mark in ("/", "\\\\", ":"))
                and not reference.endswith((".pt", ".pth", ".bin", ".safetensors", ".yaml", ".yml"))
            ):
                undeclared_bare.add(reference)
        if owner in found:
            print(f"FAIL document {owner}: self dependency", file=sys.stderr)
            return 1
        dependencies[owner] = found
        print(f"DOC {index}: {owner}; dependencies={sorted(found)}")

    # DFS over named stages; the unnamed final is a consumer, not a node.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            print(f"FAIL circular dependency involving {node}", file=sys.stderr)
            return False
        if node in visited:
            return True
        visiting.add(node)
        for dependency in dependencies[node]:
            if not visit(dependency):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    if any(not visit(name) for name in names):
        return 1

    # A declared-looking reference is valid; references that are not declared
    # remain ordinary model references and are intentionally reported, not
    # resolved or downloaded by this parser.
    print(f"OK multistage config: {len(documents)} document(s), {len(names)} named stage(s)")
    if unnamed:
        print("FINAL unnamed document: --out-path is required")
    if undeclared_bare:
        print(
            "WARN bare model reference(s) are not declared stages; verify they "
            f"are intentional model ids/paths: {sorted(undeclared_bare)}",
            file=sys.stderr,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.help_check:
        return help_check()
    return check_multistage(args.check_multistage)


if __name__ == "__main__":
    raise SystemExit(main())

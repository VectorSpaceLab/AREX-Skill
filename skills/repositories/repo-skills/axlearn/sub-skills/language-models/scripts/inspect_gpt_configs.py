#!/usr/bin/env python3
"""Inspect AXLearn GPT-family trainer configs.

This helper is read-only and safe to run from any directory. It lists exported
config names when the selected module imports successfully, and prints a helpful
message when an optional dependency is missing.

Example:
    python scripts/inspect_gpt_configs.py \
        --module axlearn.experiments.text.gpt.gala
"""

from __future__ import annotations

import argparse
import ast
import importlib
import os
from contextlib import nullcontext
from pathlib import Path


def _set_data_dir(value: str | None):
    if value is None:
        return nullcontext()
    os.environ["DATA_DIR"] = value
    return nullcontext()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, help="GPT family module to import.")
    parser.add_argument("--config", help="Optional named config to inspect.")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Optional DATA_DIR override, e.g. FAKE, for tokenizer fallbacks.",
    )
    args = parser.parse_args()

    with _set_data_dir(args.data_dir):
        try:
            module = importlib.import_module(args.module)
        except Exception as exc:  # pragma: no cover - defensive CLI guard.
            print(f"WARNING: failed to import {args.module}: {exc}")
            print(
                "Likely causes: missing optional dependency (for example tokamax/qwix), "
                "or a tokenizer/data-path issue. Falling back to static source inspection."
            )
            return _static_summary(args.module)

        named = getattr(module, "named_trainer_configs", None)
        if named is None:
            print(f"ERROR: {args.module} does not define named_trainer_configs().")
            return 2

        configs = named()
        print("Available configs:")
        for name in sorted(configs):
            print(f"- {name}")

        if args.config:
            if args.config not in configs:
                print(f"ERROR: {args.config!r} is not one of the available configs.")
                return 2
            cfg = configs[args.config]()
            print("\nResolved trainer config summary:")
            print(f"name={getattr(cfg, 'name', None)}")
            print(f"max_step={getattr(cfg, 'max_step', None)}")
            print(f"mesh_axis_names={getattr(cfg, 'mesh_axis_names', None)}")
            print(f"mesh_shape={getattr(cfg, 'mesh_shape', None)}")
            print(f"train_dtype={getattr(cfg, 'train_dtype', None)}")
    return 0


def _static_summary(module_name: str) -> int:
    try:
        import axlearn
    except Exception as exc:
        print(f"ERROR: cannot import axlearn root for static lookup: {exc}")
        return 2
    parts = module_name.split(".")
    if not parts or parts[0] != "axlearn":
        print("ERROR: static fallback only supports modules under axlearn.*")
        return 2
    path = Path(axlearn.__file__).resolve().parent.joinpath(*parts[1:]).with_suffix(".py")
    if not path.exists():
        print(f"ERROR: source file not found for {module_name}: {path}")
        return 2
    tree = ast.parse(path.read_text(encoding="utf-8"))
    print(f"Static source file: {path}")
    print("Top-level functions of interest:")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and (
            node.name in {"named_trainer_configs", "trainer_configs", "get_trainer_kwargs"}
            or node.name.endswith("_config")
        ):
            print(f"- {node.name}")
    print("Top-level constants of interest:")
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.upper() == target.id:
                    print(f"- {target.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

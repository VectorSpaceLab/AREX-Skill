#!/usr/bin/env python3
"""Inspect AXLearn vision trainer configs.

This helper is read-only and safe to run from any directory. It lists the
trainer config names exposed by a vision module and prints a short summary for a
selected config.

Example:
    python scripts/inspect_vision_configs.py \
        --module axlearn.experiments.vision.resnet.imagenet_trainer \
        --config ResNet-Test
"""

from __future__ import annotations

import argparse
import importlib
import os
from contextlib import nullcontext


def _set_data_dir(value: str | None):
    if value is None:
        return nullcontext()
    os.environ["DATA_DIR"] = value
    return nullcontext()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, help="Vision module to import.")
    parser.add_argument("--config", help="Optional config name to inspect.")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Optional DATA_DIR override, e.g. FAKE, for fake-image branches.",
    )
    args = parser.parse_args()

    with _set_data_dir(args.data_dir):
        try:
            module = importlib.import_module(args.module)
        except Exception as exc:  # pragma: no cover - defensive CLI guard.
            print(f"ERROR: failed to import {args.module}: {exc}")
            return 2

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
            print(f"input_type={type(getattr(cfg, 'input', None)).__name__}")
            print(f"model_type={type(getattr(cfg, 'model', None)).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

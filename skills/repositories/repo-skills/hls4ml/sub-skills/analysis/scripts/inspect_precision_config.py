#!/usr/bin/env python3
"""Print a tiny hls4ml name-granular config and the precision/reuse key paths.

This helper is intentionally read-only. It builds a tiny Keras model, generates
an hls4ml config, and prints the keys that matter for precision and reuse tuning.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


def add_repo_root_to_path():
    """Add the repository root to sys.path when running from the checkout."""
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "hls4ml" / "__init__.py").is_file():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return


def build_tiny_model():
    """Create a tiny Keras model for config inspection."""
    try:
        import keras
    except ImportError:  # pragma: no cover - fallback for TF-only installs
        from tensorflow import keras  # type: ignore

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(4,), name="input"),
            keras.layers.Dense(3, activation="relu", name="dense_1"),
            keras.layers.Dense(2, name="dense_2"),
        ]
    )
    # Build once so the model is fully materialized for config extraction.
    try:
        model.build((None, 4))
    except Exception:
        pass
    return model


def _pick(mapping: Mapping, *path, default=None):
    current = mapping
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def summarize_config(config):
    model_cfg = config.get("Model", {})
    layer_cfgs = config.get("LayerName", {}) or config.get("LayerType", {})

    summary = {
        "Model": {
            "Precision.default": _pick(model_cfg, "Precision", "default"),
        },
        "LayerName": {},
    }

    precision_max = _pick(model_cfg, "Precision", "maximum")
    if precision_max is not None:
        summary["Model"]["Precision.maximum"] = precision_max
    if model_cfg.get("ReuseFactor") is not None:
        summary["Model"]["ReuseFactor"] = model_cfg.get("ReuseFactor")
    if model_cfg.get("Strategy") is not None:
        summary["Model"]["Strategy"] = model_cfg.get("Strategy")

    for layer_name, layer_cfg in layer_cfgs.items():
        precision = layer_cfg.get("Precision")
        layer_summary = {}
        if layer_cfg.get("ReuseFactor") is not None:
            layer_summary["ReuseFactor"] = layer_cfg.get("ReuseFactor")
        if layer_cfg.get("Strategy") is not None:
            layer_summary["Strategy"] = layer_cfg.get("Strategy")
        if isinstance(precision, Mapping):
            for field in sorted(precision):
                layer_summary[f"Precision.{field}"] = precision[field]
        elif precision is not None:
            layer_summary["Precision.default"] = precision
        summary["LayerName"][layer_name] = layer_summary

    return summary


def print_human(summary, granularity):
    print(f"Granularity: {granularity}")
    print("\nKey paths:")
    print("  HLSConfig.Model.Precision.default")
    print("  HLSConfig.Model.ReuseFactor")
    print("  HLSConfig.LayerName.<layer>.Precision.<var>")
    print("  HLSConfig.LayerName.<layer>.ReuseFactor")
    print("  HLSConfig.LayerName.<layer>.Strategy")
    print("\nConfig summary:")
    for section, values in summary.items():
        print(section + ":")
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {values}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print the precision and reuse paths from a tiny generated hls4ml config."
    )
    parser.add_argument(
        "--backend",
        default=None,
        help="Backend name to pass into config generation, for example Vivado or Vitis.",
    )
    parser.add_argument(
        "--granularity",
        default="name",
        choices=("model", "type", "name"),
        help="Config granularity to generate. Defaults to name so per-layer keys are visible.",
    )
    parser.add_argument(
        "--default-precision",
        default="fixed<16,6>",
        help="Default precision for the model-level config.",
    )
    parser.add_argument(
        "--default-reuse-factor",
        type=int,
        default=1,
        help="Default reuse factor for the generated config.",
    )
    parser.add_argument(
        "--max-precision",
        default=None,
        help="Optional maximum precision cap passed to the config helper.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summarized config as JSON instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    add_repo_root_to_path()

    try:
        import hls4ml
    except Exception as exc:  # pragma: no cover - import failure should be explicit
        print(f"Unable to import hls4ml: {exc}", file=sys.stderr)
        return 1

    model = build_tiny_model()

    try:
        config = hls4ml.utils.config_from_keras_model(
            model,
            granularity=args.granularity,
            backend=args.backend,
            default_precision=args.default_precision,
            default_reuse_factor=args.default_reuse_factor,
            max_precision=args.max_precision,
        )
    except Exception as exc:
        print(f"Failed to generate config: {exc}", file=sys.stderr)
        return 2

    summary = summarize_config(config)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(summary, args.granularity)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

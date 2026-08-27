#!/usr/bin/env python3
"""Build or validate minimal DGL-LifeSci property-prediction JSON configs.

This helper is intentionally safe: it does not import DGL-LifeSci, download data,
train models, or instantiate predictors. It only writes known-good small config
JSON files or validates an existing JSON file against keys distilled from the
DGL-LifeSci property prediction examples.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set

COMMON_DEFAULTS: Dict[str, Any] = {
    "lr": 0.001,
    "weight_decay": 0.0,
    "patience": 30,
    "batch_size": 128,
}

MODEL_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "GCN": {
        "lr": 0.02,
        "dropout": 0.05,
        "gnn_hidden_feats": 256,
        "predictor_hidden_feats": 128,
        "num_gnn_layers": 2,
        "residual": True,
        "batchnorm": False,
    },
    "GAT": {
        "lr": 0.0003,
        "dropout": 0.05,
        "gnn_hidden_feats": 64,
        "num_heads": 8,
        "alpha": 0.06,
        "predictor_hidden_feats": 128,
        "num_gnn_layers": 5,
        "residual": True,
    },
    "Weave": {
        "lr": 0.0003,
        "num_gnn_layers": 5,
        "gnn_hidden_feats": 50,
        "graph_feats": 128,
        "gaussian_expand": True,
    },
    "MPNN": {
        "lr": 0.0003,
        "node_out_feats": 64,
        "edge_hidden_feats": 128,
        "num_step_message_passing": 6,
        "num_step_set2set": 6,
        "num_layer_set2set": 3,
    },
    "AttentiveFP": {
        "lr": 0.0003,
        "num_layers": 2,
        "num_timesteps": 2,
        "graph_feat_size": 200,
        "dropout": 0.0,
    },
    "NF": {
        "lr": 0.01,
        "weight_decay": 0.001,
        "batch_size": 512,
        "gnn_hidden_feats": 32,
        "num_gnn_layers": 2,
        "batchnorm": False,
        "dropout": 0.15,
        "predictor_hidden_feats": 32,
    },
    "gin_supervised_contextpred": {
        "lr": 0.02,
        "jk": "last",
        "readout": "sum",
    },
    "gin_supervised_edgepred": {
        "lr": 0.02,
        "jk": "last",
        "readout": "sum",
    },
    "gin_supervised_infomax": {
        "lr": 0.02,
        "jk": "last",
        "readout": "sum",
    },
    "gin_supervised_masking": {
        "lr": 0.02,
        "jk": "last",
        "readout": "sum",
    },
}

MODEL_KEY_DESCRIPTIONS: Dict[str, Set[str]] = {
    "GCN": {"gnn_hidden_feats", "predictor_hidden_feats", "num_gnn_layers", "residual", "batchnorm", "dropout"},
    "GAT": {"gnn_hidden_feats", "num_heads", "alpha", "predictor_hidden_feats", "num_gnn_layers", "residual", "dropout"},
    "Weave": {"num_gnn_layers", "gnn_hidden_feats", "graph_feats", "gaussian_expand"},
    "MPNN": {"node_out_feats", "edge_hidden_feats", "num_step_message_passing", "num_step_set2set", "num_layer_set2set"},
    "AttentiveFP": {"num_layers", "num_timesteps", "graph_feat_size", "dropout"},
    "NF": {"gnn_hidden_feats", "num_gnn_layers", "batchnorm", "dropout", "predictor_hidden_feats"},
    "gin_supervised_contextpred": {"jk", "readout"},
    "gin_supervised_edgepred": {"jk", "readout"},
    "gin_supervised_infomax": {"jk", "readout"},
    "gin_supervised_masking": {"jk", "readout"},
}

COMMON_KEYS = set(COMMON_DEFAULTS)
ALLOWED_KEYS: Dict[str, Set[str]] = {
    model: COMMON_KEYS | model_keys for model, model_keys in MODEL_KEY_DESCRIPTIONS.items()
}

POSITIVE_NUMERIC_KEYS = {"lr", "batch_size", "patience"}
NONNEGATIVE_NUMERIC_KEYS = {"weight_decay", "dropout", "alpha"}
BOOLEAN_KEYS = {"residual", "batchnorm", "gaussian_expand"}
CHOICES = {
    "jk": {"concat", "last", "max", "sum"},
    "readout": {"sum", "mean", "max", "attention"},
}


def available_models() -> str:
    return ", ".join(MODEL_DEFAULTS)


def build_config(model: str, overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    if model not in MODEL_DEFAULTS:
        raise ValueError(f"Unsupported model {model!r}. Choose one of: {available_models()}")

    config: Dict[str, Any] = dict(COMMON_DEFAULTS)
    config.update(MODEL_DEFAULTS[model])
    if overrides:
        unknown = set(overrides) - ALLOWED_KEYS[model]
        if unknown:
            raise ValueError(
                f"Unsupported key(s) for {model}: {', '.join(sorted(unknown))}. "
                f"Allowed keys: {', '.join(sorted(ALLOWED_KEYS[model]))}"
            )
        config.update(overrides)
    validate_config(model, config)
    return config


def load_json(path: Path) -> Dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def parse_override(values: Iterable[str]) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Override {item!r} must use KEY=JSON_VALUE format")
        key, raw_value = item.split("=", 1)
        if not key:
            raise ValueError(f"Override {item!r} has an empty key")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        overrides[key] = value
    return overrides


def ensure_number(config: Mapping[str, Any], key: str, *, positive: bool) -> None:
    if key not in config:
        return
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric, got {type(value).__name__}")
    if positive and value <= 0:
        raise ValueError(f"{key} must be > 0")
    if not positive and value < 0:
        raise ValueError(f"{key} must be >= 0")


def validate_config(model: str, config: Mapping[str, Any]) -> None:
    if model not in ALLOWED_KEYS:
        raise ValueError(f"Unsupported model {model!r}. Choose one of: {available_models()}")

    unknown = set(config) - ALLOWED_KEYS[model]
    if unknown:
        raise ValueError(
            f"Unsupported key(s) for {model}: {', '.join(sorted(unknown))}. "
            f"Allowed keys: {', '.join(sorted(ALLOWED_KEYS[model]))}"
        )

    missing_common = COMMON_KEYS - set(config)
    if missing_common:
        raise ValueError(f"Missing common key(s): {', '.join(sorted(missing_common))}")

    for key in POSITIVE_NUMERIC_KEYS:
        ensure_number(config, key, positive=True)
    for key in NONNEGATIVE_NUMERIC_KEYS:
        ensure_number(config, key, positive=False)

    for key in BOOLEAN_KEYS:
        if key in config and not isinstance(config[key], bool):
            raise ValueError(f"{key} must be a JSON boolean")

    for key, allowed in CHOICES.items():
        if key in config and config[key] not in allowed:
            raise ValueError(f"{key} must be one of {', '.join(sorted(allowed))}")

    for key in [
        "num_gnn_layers",
        "num_heads",
        "node_out_feats",
        "edge_hidden_feats",
        "num_step_message_passing",
        "num_step_set2set",
        "num_layer_set2set",
        "num_layers",
        "num_timesteps",
        "graph_feat_size",
        "gnn_hidden_feats",
        "predictor_hidden_feats",
        "graph_feats",
    ]:
        if key in config:
            value = config[key]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{key} must be a positive integer")


def write_json(path: Path, config: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or validate minimal DGL-LifeSci property-prediction JSON configs without training or downloads."
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=sorted(MODEL_DEFAULTS),
        help="Model/config family to build or validate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write a generated config JSON to this path.",
    )
    parser.add_argument(
        "--validate",
        type=Path,
        help="Validate an existing JSON config for the selected model.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=JSON_VALUE",
        help="Override a generated config value, for example --override batch_size=64 --override dropout=0.1.",
    )
    parser.add_argument(
        "--print",
        dest="print_config",
        action="store_true",
        help="Print the generated or validated config to stdout.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        if args.validate:
            config = load_json(args.validate)
            validate_config(args.model, config)
            message = f"Validated {args.validate} for {args.model} with {len(config)} keys."
        else:
            overrides = parse_override(args.override)
            config = build_config(args.model, overrides)
            message = f"Built config for {args.model} with {len(config)} keys."

        if args.output:
            write_json(args.output, config)
            message += f" Wrote {args.output}."

        if args.print_config:
            print(json.dumps(config, indent=2, sort_keys=True))
        else:
            print(message)
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

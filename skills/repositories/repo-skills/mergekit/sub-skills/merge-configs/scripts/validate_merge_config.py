#!/usr/bin/env python3
"""Parse and validate a mergekit YAML config without resolving model files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate mergekit YAML schema and registered method names without "
            "downloading or loading model checkpoints."
        )
    )
    parser.add_argument("config", type=Path, help="YAML configuration file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable validation summary",
    )
    return parser


def summary(config: Any) -> dict[str, Any]:
    topology = [name for name in ("models", "slices", "modules") if getattr(config, name)]
    return {
        "merge_method": config.merge_method,
        "topology": topology[0] if len(topology) == 1 else topology,
        "referenced_models": [str(model) for model in config.referenced_models()],
        "has_base_model": config.base_model is not None,
        "has_tokenizer": config.tokenizer is not None or config.tokenizer_source is not None,
        "has_chat_template": config.chat_template is not None,
        "dtype": config.dtype,
        "out_dtype": config.out_dtype,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment failure path
        print(f"INVALID: PyYAML is unavailable: {exc}", file=sys.stderr)
        return 2

    try:
        from mergekit.config import MergeConfiguration
        from mergekit.merge_methods import REGISTERED_MERGE_METHODS
    except ImportError as exc:  # pragma: no cover - environment failure path
        print(f"INVALID: mergekit is unavailable: {exc}", file=sys.stderr)
        return 2

    if not args.config.is_file():
        print(f"INVALID: config file does not exist: {args.config}", file=sys.stderr)
        return 2

    try:
        with args.config.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
        if not isinstance(raw, dict):
            raise ValueError("top-level YAML value must be a mapping")
        config = MergeConfiguration.model_validate(raw)
        topology = [name for name in ("models", "slices", "modules") if getattr(config, name)]
        if len(topology) != 1:
            raise ValueError("exactly one of models, slices, or modules must be populated")
        if config.merge_method not in REGISTERED_MERGE_METHODS:
            names = ", ".join(sorted(REGISTERED_MERGE_METHODS))
            raise ValueError(
                f"unregistered merge_method {config.merge_method!r}; available: {names}"
            )
        result = summary(config)
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("VALID: mergekit YAML schema")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

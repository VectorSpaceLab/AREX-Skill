#!/usr/bin/env python3
"""Build a YiVal YAML template with built-in registries imported."""

from __future__ import annotations

import argparse
from pathlib import Path

# Import built-ins that register common components.
import yival.cli.init  # noqa: F401
from yival.cli.utils import generate_experiment_config_yaml
from yival.schemas.experiment_config import WrapperConfig, WrapperVariation


def parse_variation(spec: str) -> WrapperConfig:
    """Parse name=value1,value2 into a WrapperConfig of string variations."""
    if "=" not in spec:
        raise argparse.ArgumentTypeError("variation must be name=value1,value2")
    name, values = spec.split("=", 1)
    variations = [WrapperVariation(value_type="str", value=value) for value in values.split(",")]
    return WrapperConfig(name=name, variations=variations)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="YAML path to write")
    parser.add_argument("--function", required=True, help="custom function import path")
    parser.add_argument("--source-type", default="dataset", choices=["dataset", "machine_generated", "user"])
    parser.add_argument("--reader", default=None, help="reader id such as csv_reader")
    parser.add_argument("--evaluator", action="append", default=[], help="evaluator id; repeatable")
    parser.add_argument("--data-generator", action="append", default=[], help="data generator id; repeatable")
    parser.add_argument("--selection-strategy", default=None, help="selection strategy id such as ahp_selection")
    parser.add_argument("--enhancer", default=None, help="enhancer id")
    parser.add_argument("--variation", action="append", type=parse_variation, default=[], help="manual string variation, e.g. task='prompt a','prompt b'")
    args = parser.parse_args()

    yaml_text = generate_experiment_config_yaml(
        custom_function=args.function,
        source_type="user_input" if args.source_type == "user" else args.source_type,
        evaluator_names=args.evaluator or None,
        reader_name=args.reader,
        enhancer_name=args.enhancer,
        data_generator_names=args.data_generator or None,
        selection_strategy_name=args.selection_strategy,
        wrapper_configs=args.variation or None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml_text, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

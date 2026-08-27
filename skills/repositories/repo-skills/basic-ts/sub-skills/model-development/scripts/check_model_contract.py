#!/usr/bin/env python3
"""Inspect a BasicTS model contract and optionally run a tiny dummy forward.

This helper is read-only by default. It prints the imported model class,
its forward signature, and the accepted keyword arguments. If a config class
and dummy input shape are provided, it can also run a tiny forward pass.

Examples:
    python scripts/check_model_contract.py --model-module basicts.models.DLinear --model-class DLinear
    python scripts/check_model_contract.py --model-module basicts.models.DLinear --model-class DLinear \
        --config-module basicts.models.DLinear --config-class DLinearConfig \
        --config-json '{"input_len": 8, "output_len": 4, "num_features": 2}' \
        --dummy-shape 2 8 2
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from dataclasses import asdict, is_dataclass
from typing import Any

import torch


def load_attr(module_name: str, attr_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def make_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON input must decode to an object/dict.")
    return parsed


def build_model(model_cls, config_obj=None):
    if config_obj is None:
        try:
            return model_cls()
        except TypeError as exc:
            raise TypeError(
                f"Could not instantiate {model_cls.__name__} without a config object. "
                "Pass --config-module/--config-class and --config-json."
            ) from exc
    return model_cls(config_obj)


def format_signature(obj) -> str:
    return str(inspect.signature(obj))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a BasicTS model contract.")
    parser.add_argument("--model-module", required=True, help="Module that exports the model class.")
    parser.add_argument("--model-class", required=True, help="Model class name to inspect.")
    parser.add_argument("--config-module", help="Optional module that exports the config class.")
    parser.add_argument("--config-class", help="Optional config class name to instantiate.")
    parser.add_argument("--config-json", help="JSON object with kwargs for the config class.")
    parser.add_argument("--dummy-shape", nargs=3, type=int, metavar=("B", "T", "C"), help="Optional dummy input shape.")
    parser.add_argument("--forward-json", help="JSON object with extra kwargs for the forward call.")
    args = parser.parse_args()

    model_cls = load_attr(args.model_module, args.model_class)
    print(f"model={model_cls.__module__}.{model_cls.__name__}")
    print(f"model_init_signature={format_signature(model_cls)}")
    print(f"forward_signature={format_signature(model_cls.forward)}")

    forward_params = list(inspect.signature(model_cls.forward).parameters)
    print(f"forward_params={forward_params}")
    print(f"has_inputs={'inputs' in forward_params}")

    config_obj = None
    if args.config_module and args.config_class:
        config_cls = load_attr(args.config_module, args.config_class)
        config_kwargs = make_json(args.config_json)
        print(f"config={config_cls.__module__}.{config_cls.__name__}")
        print(f"config_kwargs={sorted(config_kwargs.keys())}")
        try:
            config_obj = config_cls(**config_kwargs)
            if is_dataclass(config_obj):
                print(f"config_dataclass_fields={sorted(asdict(config_obj).keys())[:12]}")
            else:
                print("config_instantiated=true")
        except Exception as exc:  # pragma: no cover - inspection helper
            print(f"config_error={type(exc).__name__}: {exc}")
            return 1

    if args.dummy_shape is not None:
        forward_kwargs = make_json(args.forward_json)
        print(f"forward_kwargs_keys={sorted(forward_kwargs.keys())}")
        try:
            model = build_model(model_cls, config_obj)
            model.eval()
            dummy = torch.randn(*args.dummy_shape)
            accepted = set(inspect.signature(model.forward).parameters)
            accepted.discard("self")
            accepted.discard("inputs")
            call_kwargs = {k: v for k, v in forward_kwargs.items() if k in accepted}
            with torch.no_grad():
                result = model(dummy, **call_kwargs)
            if isinstance(result, torch.Tensor):
                print(f"forward_result=tensor shape={tuple(result.shape)} dtype={result.dtype}")
            elif isinstance(result, dict):
                print(f"forward_result=dict keys={sorted(result.keys())}")
                if "prediction" in result and isinstance(result["prediction"], torch.Tensor):
                    print(f"prediction_shape={tuple(result['prediction'].shape)}")
            else:
                print(f"forward_result={type(result).__name__}")
        except Exception as exc:  # pragma: no cover - inspection helper
            print(f"forward_error={type(exc).__name__}: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

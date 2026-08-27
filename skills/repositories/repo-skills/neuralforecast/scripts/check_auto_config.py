#!/usr/bin/env python3
"""Check NeuralForecast Auto* configuration objects.

Purpose:
- Confirm that Auto* wrappers and backend option objects import and expose the
  expected configuration shape without running a long search.
- Keep the check safe and local.

Prerequisites:
- NeuralForecast, Ray, and Optuna installed in the active environment.

Example:
    python scripts/check_auto_config.py
"""

from __future__ import annotations

import argparse
import inspect


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def main() -> int:
    build_parser().parse_args()

    from neuralforecast.auto import AutoMLP, AutoNHITS
    from neuralforecast.common._base_auto import BaseAuto, OptunaOptions, RayOptions
    from neuralforecast.common._base_model import DistributedConfig

    print("BaseAuto:", inspect.signature(BaseAuto))
    print("AutoNHITS:", inspect.signature(AutoNHITS))
    print("AutoMLP:", inspect.signature(AutoMLP))
    print("RayOptions:", inspect.signature(RayOptions))
    print("OptunaOptions:", inspect.signature(OptunaOptions))
    print("DistributedConfig:", inspect.signature(DistributedConfig))

    default = AutoMLP.default_config.copy()
    assert "input_size_multiplier" in default
    normalized = default.copy()
    normalized.update({"h": 12, "max_steps": 1, "val_check_steps": 1, "input_size_multiplier": 1})
    assert normalized["h"] == 12
    print("AutoMLP default config keys:", sorted(default.keys()))
    print("AutoMLP normalized keys:", sorted(normalized.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

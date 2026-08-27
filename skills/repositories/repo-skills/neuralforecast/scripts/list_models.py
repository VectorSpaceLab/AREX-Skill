#!/usr/bin/env python3
"""List NeuralForecast model families and capability flags.

Purpose:
- Show the public model catalog from the installed package.
- Surface optional-dependency and capability flags without needing the source checkout.

Prerequisites:
- NeuralForecast installed in the active environment.

Example:
    python scripts/list_models.py
    python scripts/list_models.py --json
"""

from __future__ import annotations

import argparse
import json
import inspect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of a table.")
    return parser


def describe_model(cls) -> dict[str, object]:
    module = inspect.getmodule(cls)
    return {
        "module": cls.__module__,
        "exogenous_futr": getattr(cls, "EXOGENOUS_FUTR", None),
        "exogenous_hist": getattr(cls, "EXOGENOUS_HIST", None),
        "exogenous_stat": getattr(cls, "EXOGENOUS_STAT", None),
        "exogenous_cat": getattr(cls, "EXOGENOUS_CAT", None),
        "multivariate": getattr(cls, "MULTIVARIATE", None),
        "recurrent": getattr(cls, "RECURRENT", None),
        "optional_dependency_flag": next(
            (name for name in ("IS_TRANSFORMERS_INSTALLED", "IS_XLSTM_INSTALLED") if hasattr(module, name)),
            None,
        ),
        "optional_dependency_value": next(
            (getattr(module, name) for name in ("IS_TRANSFORMERS_INSTALLED", "IS_XLSTM_INSTALLED") if hasattr(module, name)),
            None,
        ),
    }


def main() -> int:
    args = build_parser().parse_args()
    from neuralforecast import models

    rows = []
    for name in getattr(models, "__all__", []):
        cls = getattr(models, name, None)
        if cls is None:
            continue
        rows.append((name, describe_model(cls)))

    if args.json:
        print(json.dumps({name: info for name, info in rows}, indent=2, sort_keys=True, default=str))
        return 0

    header = f"{'Model':<20} {'Family flags':<34} {'Optional deps':<20}"
    print(header)
    print("-" * len(header))
    for name, info in rows:
        flags = []
        for key in ("multivariate", "recurrent", "exogenous_futr", "exogenous_hist", "exogenous_stat", "exogenous_cat"):
            if info[key]:
                flags.append(key.replace("exogenous_", "exog-").replace("_", "-"))
        dep = ""
        if info["optional_dependency_flag"]:
            dep = f"{info['optional_dependency_flag']}={info['optional_dependency_value']}"
        print(f"{name:<20} {', '.join(flags):<34} {dep:<20}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Print the StatsForecast model groups and a JSON snapshot.

This helper is safe to run locally. It only inspects the installed
``statsforecast`` package and does not modify data or network resources.
"""

from __future__ import annotations

import argparse
import json
from importlib.util import find_spec
from inspect import signature
from typing import Any, Dict, List, Optional

from statsforecast import models as sf_models

MODEL_GROUPS = [
    {
        "name": "automatic forecasting",
        "models": [
            "AutoARIMA",
            "AutoETS",
            "AutoCES",
            "AutoTheta",
            "AutoMFLES",
            "AutoTBATS",
        ],
    },
    {
        "name": "arima family",
        "models": ["ARIMA", "AutoRegressive"],
    },
    {
        "name": "exponential smoothing",
        "models": [
            "SimpleExponentialSmoothing",
            "SimpleExponentialSmoothingOptimized",
            "SeasonalExponentialSmoothing",
            "SeasonalExponentialSmoothingOptimized",
            "Holt",
            "HoltWinters",
        ],
    },
    {
        "name": "baselines",
        "models": [
            "HistoricAverage",
            "Naive",
            "RandomWalkWithDrift",
            "SeasonalNaive",
            "WindowAverage",
            "SeasonalWindowAverage",
        ],
    },
    {
        "name": "sparse or intermittent demand",
        "models": ["ADIDA", "CrostonClassic", "CrostonOptimized", "CrostonSBA", "IMAPA", "TSB"],
    },
    {
        "name": "multiple seasonalities",
        "models": ["MSTL", "MFLES", "TBATS"],
    },
    {
        "name": "theta family",
        "models": ["Theta", "OptimizedTheta", "DynamicTheta", "DynamicOptimizedTheta"],
    },
    {
        "name": "volatility",
        "models": ["GARCH", "ARCH"],
    },
    {
        "name": "machine learning wrapper",
        "models": ["SklearnModel"],
    },
    {
        "name": "fallbacks",
        "models": ["ConstantModel", "ZeroModel", "NaNModel"],
    },
    {
        "name": "advanced state-space",
        "models": ["UCM"],
    },
]

EXOGENOUS_MODELS = {
    "AutoARIMA",
    "ARIMA",
    "AutoRegressive",
    "AutoMFLES",
    "MFLES",
    "SklearnModel",
    "UCM",
}

OPTIONAL_ADAPTER = {
    "name": "AutoARIMAProphet",
    "module": "statsforecast.adapters.prophet",
    "dependency": "prophet",
}

OPTIONAL_NOTES = [
    {
        "name": "scikit-learn",
        "used_by": ["AutoMFLES", "SklearnModel"],
        "note": "required for AutoMFLES construction and SklearnModel fit/forecast calls",
    },
    {
        "name": "prophet",
        "used_by": ["AutoARIMAProphet"],
        "note": "optional adapter only; not part of the core model catalog",
    },
]


def model_info(name: str) -> Dict[str, Any]:
    cls = getattr(sf_models, name)
    sig_obj = signature(cls)
    sig = str(sig_obj)
    default_alias: Optional[str] = None
    alias_param = sig_obj.parameters.get("alias")
    if alias_param is not None and alias_param.default is not alias_param.empty:
        default = alias_param.default
        if default is None:
            default_alias = None
        else:
            default_alias = str(default)
    return {
        "name": name,
        "signature": sig,
        "default_alias": default_alias,
        "uses_exog": name in EXOGENOUS_MODELS,
        "has_forward": hasattr(cls, "forward"),
        "has_simulate": hasattr(cls, "simulate"),
        "has_prediction_intervals": "prediction_intervals" in sig_obj.parameters,
    }


def prophet_adapter_available() -> bool:
    if find_spec("prophet") is None and find_spec("fbprophet") is None:
        return False
    try:
        from statsforecast.adapters.prophet import AutoARIMAProphet  # noqa: F401
    except Exception:
        return False
    return True


def build_catalog() -> Dict[str, Any]:
    groups = []
    for group in MODEL_GROUPS:
        groups.append(
            {
                "name": group["name"],
                "models": [model_info(name) for name in group["models"]],
            }
        )

    return {
        "groups": groups,
        "optional_notes": OPTIONAL_NOTES,
        "optional_adapter": {
            **OPTIONAL_ADAPTER,
            "available": prophet_adapter_available(),
        },
    }


def render_text(catalog: Dict[str, Any]) -> str:
    lines: List[str] = ["StatsForecast model groups", ""]
    for group in catalog["groups"]:
        lines.append(group["name"].title())
        for model in group["models"]:
            flags = []
            if model["uses_exog"]:
                flags.append("exog")
            if model["has_forward"]:
                flags.append("forward")
            if model["has_simulate"]:
                flags.append("simulate")
            if model["has_prediction_intervals"]:
                flags.append("prediction_intervals")
            flag_text = f" [{' | '.join(flags)}]" if flags else ""
            lines.append(f"- {model['name']}{flag_text}")
            lines.append(f"  {model['signature']}")
        lines.append("")

    lines.append("Optional dependencies")
    for item in catalog["optional_notes"]:
        lines.append(f"- {item['name']}: {item['note']} ({', '.join(item['used_by'])})")
    adapter = catalog["optional_adapter"]
    status = "available" if adapter["available"] else "not installed"
    lines.append(
        f"- {adapter['name']}: {status}; module {adapter['module']} (dependency: {adapter['dependency']})"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the StatsForecast model catalog grouped by family."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    catalog = build_catalog()
    if args.json:
        print(json.dumps(catalog, indent=2, sort_keys=False))
    else:
        print(render_text(catalog))


if __name__ == "__main__":
    main()

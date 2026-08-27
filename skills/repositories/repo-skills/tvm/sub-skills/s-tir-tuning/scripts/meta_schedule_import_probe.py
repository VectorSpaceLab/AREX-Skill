#!/usr/bin/env python3
"""Probe TVM S-TIR/meta-schedule imports and signatures without tuning."""
from __future__ import annotations

import argparse
import inspect
import json
from importlib import util


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    import tvm
    import tvm.s_tir as s_tir

    result = {
        "tvm_version": getattr(tvm, "__version__", None),
        "schedule_signature": str(inspect.signature(s_tir.Schedule)),
        "has_transform": hasattr(s_tir, "transform"),
        "has_dlight": hasattr(s_tir, "dlight"),
        "has_meta_schedule": hasattr(s_tir, "meta_schedule"),
        "xgboost_available": util.find_spec("xgboost") is not None,
    }
    if result["has_meta_schedule"]:
        ms = s_tir.meta_schedule
        result["tune_tir_signature"] = str(inspect.signature(ms.tune_tir))
        for name in ["Builder", "Runner", "Database", "TuneContext"]:
            result[f"has_{name}"] = hasattr(ms, name)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

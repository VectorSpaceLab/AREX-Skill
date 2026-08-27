#!/usr/bin/env python3
"""Check a Python environment for PyPSA runtime readiness.

The helper imports PyPSA, mandatory dependencies, selected optional extras, and
optionally runs a tiny HiGHS optimization smoke. It performs no network access
and writes no files.

Examples:
    python check_pypsa_environment.py
    python check_pypsa_environment.py --optional --solve-smoke
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import warnings
from importlib import import_module

logging.getLogger("pypsa.version").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore",
    message=r"pandas infers the `str` dtype for string data since its version 3\.0.*",
    category=FutureWarning,
)

MANDATORY_IMPORTS = [
    "pypsa",
    "numpy",
    "pandas",
    "xarray",
    "netCDF4",
    "linopy",
    "highspy",
    "matplotlib",
    "plotly",
    "pydeck",
    "seaborn",
    "geopandas",
    "shapely",
    "networkx",
]

OPTIONAL_IMPORTS = {
    "hdf5": ["tables"],
    "excel": ["openpyxl", "python_calamine"],
    "cloudpath": ["cloudpathlib"],
    "cartopy": ["cartopy"],
    "sklearn-spatial-clustering": ["sklearn"],
    "tsam-temporal-segmentation": ["tsam"],
    "pandapower-converter": ["pandapower"],
    "pypower-converter": ["pypower"],
    "dotenv-options": ["dotenv"],
    "gurobi-solver-api": ["gurobipy"],
}


def import_status(module_name: str) -> dict[str, str | bool]:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return {"module": module_name, "available": False, "detail": "not installed"}
    try:
        module = import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {
            "module": module_name,
            "available": False,
            "detail": f"import failed: {type(exc).__name__}: {exc}",
        }
    version = getattr(module, "__version__", None)
    return {
        "module": module_name,
        "available": True,
        "detail": str(version) if version else "imported",
    }


def solve_smoke() -> dict[str, str | float]:
    import pandas as pd
    import pypsa

    snapshots = pd.date_range("2024-01-01", periods=2, freq="h")
    n = pypsa.Network()
    n.set_snapshots(snapshots)
    n.add("Carrier", "AC")
    n.add("Carrier", "gas")
    n.add("Bus", "bus", carrier="AC")
    n.add("Load", "load", bus="bus", carrier="AC", p_set=[5.0, 6.0])
    n.add("Generator", "gen", bus="bus", carrier="gas", p_nom=10.0, marginal_cost=20.0)
    n.consistency_check(strict=["unknown_buses", "unknown_carriers"])
    status, condition = n.optimize(
        solver_name="highs",
        log_to_console=False,
        include_objective_constant=False,
    )
    return {
        "status": status,
        "condition": condition,
        "objective": float(n.objective),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PyPSA imports and optional extras.")
    parser.add_argument(
        "--optional",
        action="store_true",
        help="Also report optional-extra module availability.",
    )
    parser.add_argument(
        "--solve-smoke",
        action="store_true",
        help="Run a tiny HiGHS optimization smoke after imports succeed.",
    )
    args = parser.parse_args()

    report: dict[str, object] = {
        "mandatory": [import_status(module) for module in MANDATORY_IMPORTS],
    }
    missing_mandatory = [
        row["module"] for row in report["mandatory"] if not row["available"]  # type: ignore[index]
    ]

    if args.optional:
        report["optional"] = {
            feature: [import_status(module) for module in modules]
            for feature, modules in OPTIONAL_IMPORTS.items()
        }

    if args.solve_smoke and not missing_mandatory:
        report["solve_smoke"] = solve_smoke()

    print(json.dumps(report, indent=2, sort_keys=True))
    if missing_mandatory:
        raise SystemExit(f"Missing mandatory imports: {missing_mandatory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

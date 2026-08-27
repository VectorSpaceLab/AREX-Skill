#!/usr/bin/env python3
"""Check an installed Mesa runtime and selected optional extras.

This helper is safe to run from any working directory. It imports the installed
Mesa package, probes important public modules, optionally requires network and
visualization extras, and prints a JSON report.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from importlib import metadata
from typing import Any

CORE_MODULES = [
    "mesa",
    "mesa.discrete_space",
    "mesa.time",
    "mesa.datacollection",
    "mesa.experimental.scenarios",
]
NETWORK_MODULES = ["networkx"]
VIZ_MODULES = ["mesa.visualization", "solara", "matplotlib", "altair"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe an installed Mesa package and optional extras, then emit JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--require-core", action="store_true", help="Require all core Mesa module checks to pass.")
    parser.add_argument("--require-network", action="store_true", help="Require NetworkX/network extra readiness.")
    parser.add_argument("--require-viz", action="store_true", help="Require visualization extra readiness.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def import_probe(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except BaseException as exc:  # noqa: BLE001 - report import-time failures as JSON.
        return {"ok": False, "module": module_name, "error": f"{type(exc).__name__}: {exc}"}

    version = getattr(module, "__version__", None)
    return {"ok": True, "module": module_name, "version": str(version) if version is not None else None}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def smoke_core() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False}
    try:
        import mesa
        from mesa import Agent, DataCollector, Model
        from mesa.discrete_space import OrthogonalMooreGrid
        from mesa.time import Schedule
        from mesa.visualization import SolaraViz, make_plot_component, make_space_component
    except BaseException as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    try:
        model = Model(rng=42)
        agent = Agent(model)
        grid = OrthogonalMooreGrid((3, 3), torus=True, random=model.random)
        cell = grid.select_random_empty_cell()
        dc = DataCollector(model_reporters={"n_agents": lambda m: len(m.agents)})
        dc.collect(model)
        result.update(
            {
                "ok": True,
                "mesa_version": getattr(mesa, "__version__", None),
                "distribution_version": dist_version("Mesa"),
                "agent_id": agent.unique_id,
                "agent_count": len(model.agents),
                "grid_cell_count": len(grid.all_cells),
                "selected_cell": list(cell.coordinate),
                "datacollector_rows": int(len(dc.get_model_vars_dataframe())),
                "signatures": {
                    "Model": str(inspect.signature(Model)),
                    "Agent": str(inspect.signature(Agent)),
                    "DataCollector": str(inspect.signature(DataCollector)),
                    "Schedule": str(inspect.signature(Schedule)),
                    "SolaraViz": str(inspect.signature(SolaraViz)),
                    "make_space_component": str(inspect.signature(make_space_component)),
                    "make_plot_component": str(inspect.signature(make_plot_component)),
                },
            }
        )
    except BaseException as exc:  # noqa: BLE001
        result.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report: dict[str, Any] = {
        "python": {"version": platform.python_version(), "requires_python": ">=3.12"},
        "modules": {},
        "smoke": {},
        "actions": [],
        "status": "ok",
    }

    if sys.version_info < (3, 12):
        report["actions"].append("Use Python 3.12 or newer for this Mesa snapshot.")

    for name in CORE_MODULES:
        report["modules"][name] = import_probe(name)
    for name in NETWORK_MODULES:
        report["modules"][name] = import_probe(name)
    for name in VIZ_MODULES:
        report["modules"][name] = import_probe(name)

    report["smoke"]["core"] = smoke_core()

    failures: list[str] = []
    if args.require_core:
        for name in CORE_MODULES:
            if not report["modules"][name]["ok"]:
                failures.append(f"core import failed: {name}")
        if not report["smoke"]["core"].get("ok"):
            failures.append("core smoke failed")
    if args.require_network and not report["modules"]["networkx"]["ok"]:
        failures.append("network extra missing: networkx")
        report["actions"].append("Install network extras with: python -m pip install 'mesa[network]'.")
    if args.require_viz:
        for name in VIZ_MODULES:
            if not report["modules"][name]["ok"]:
                failures.append(f"visualization import failed: {name}")
        if failures:
            report["actions"].append("Install visualization extras with: python -m pip install 'mesa[viz]' or 'mesa[rec]'.")

    if sys.version_info < (3, 12) or failures:
        report["status"] = "failed"
    elif not report["smoke"]["core"].get("ok"):
        report["status"] = "degraded"
    elif any(not item["ok"] for item in report["modules"].values()):
        report["status"] = "degraded"

    if failures:
        report["failures"] = sorted(set(failures))

    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inspect Isaac Lab simulation-launcher APIs and backend config shapes."""

from __future__ import annotations

import argparse
import inspect
import json

from isaaclab.app import AppLauncher, get_settings_manager, initialize_carb_settings
from isaaclab.physics.physics_manager_cfg import PhysicsCfg
from isaaclab.renderers.renderer_cfg import RendererCfg
from isaaclab.sim.simulation_cfg import SimulationCfg
from isaaclab_tasks.utils import add_launcher_args
from isaaclab_tasks.utils.sim_launcher import compute_kit_requirements, launch_simulation, validate_runtime_compatibility


def _signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - helper script
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Isaac Lab simulation APIs.")
    add_launcher_args(parser)
    args = parser.parse_args()

    report = {
        "AppLauncher": {
            "init": _signature(AppLauncher.__init__),
            "add_app_launcher_args": _signature(AppLauncher.add_app_launcher_args),
        },
        "SettingsManager": {
            "type": type(get_settings_manager()).__name__,
            "initialize_carb_settings": _signature(initialize_carb_settings),
        },
        "SimulationCfg": {
            "signature": _signature(SimulationCfg),
            "physics_field": type(getattr(SimulationCfg, "physics", None)).__name__,
            "visualizer_field": type(getattr(SimulationCfg, "visualizer_cfgs", None)).__name__,
        },
        "BackendCfgs": {
            "PhysicsCfg": _signature(PhysicsCfg),
            "RendererCfg": _signature(RendererCfg),
        },
        "Helpers": {
            "add_launcher_args": _signature(add_launcher_args),
            "compute_kit_requirements": _signature(compute_kit_requirements),
            "validate_runtime_compatibility": _signature(validate_runtime_compatibility),
            "launch_simulation": _signature(launch_simulation),
        },
        "launcher_args_seen": sorted(vars(args).keys()),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

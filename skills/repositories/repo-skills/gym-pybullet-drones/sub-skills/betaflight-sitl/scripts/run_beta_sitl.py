#!/usr/bin/env python3
"""Safe-by-default wrapper for the gym-pybullet-drones Betaflight SITL workflow.

By default the helper performs a read-only layout check and exits. Pass
--execute only after the external Betaflight SITL tree exists and the user
explicitly wants the SITL workflow to run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from check_betaflight_layout import inspect_layout

DRONE_CHOICES = ("cf2x", "cf2p", "racer")
PHYSICS_CHOICES = ("pyb", "dyn", "pyb_gnd", "pyb_drag", "pyb_dw", "pyb_gnd_drag_dw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or preflight the gym-pybullet-drones Betaflight SITL workflow.")
    parser.add_argument("--base-dir", default=None, help="Betaflight SITL base directory. Defaults to the package-relative location that BetaAviary expects.")
    parser.add_argument("--num-drones", type=int, default=2, help="Number of drones/SITL instances to use.")
    parser.add_argument("--drone", choices=DRONE_CHOICES, default="racer", help="Drone model value passed to BetaAviary and beta.py.")
    parser.add_argument("--physics", choices=PHYSICS_CHOICES, default="pyb", help="Physics mode passed to BetaAviary and beta.py.")
    parser.add_argument("--duration-sec", type=float, default=5.0, help="Execution duration when --execute is passed.")
    parser.add_argument("--output-folder", default="beta-results", help="Logger output folder for execution mode.")
    parser.add_argument("--simulation-freq-hz", type=int, default=500, help="PyBullet frequency for execution mode.")
    parser.add_argument("--control-freq-hz", type=int, default=500, help="Control frequency for execution mode.")
    gui_group = parser.add_mutually_exclusive_group()
    gui_group.add_argument("--gui", dest="gui", action="store_true", help="Enable PyBullet GUI during execution.")
    gui_group.add_argument("--no-gui", dest="gui", action="store_false", help="Run headless during execution.")
    parser.set_defaults(gui=False)
    plot_group = parser.add_mutually_exclusive_group()
    plot_group.add_argument("--plot", dest="plot", action="store_true", help="Enable logger plotting after execution.")
    plot_group.add_argument("--no-plot", dest="plot", action="store_false", help="Disable logger plotting after execution.")
    parser.set_defaults(plot=False)
    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument("--user-debug-gui", dest="user_debug_gui", action="store_true", help="Enable PyBullet user debug GUI in execution mode.")
    debug_group.add_argument("--no-user-debug-gui", dest="user_debug_gui", action="store_false", help="Disable PyBullet user debug GUI in execution mode.")
    parser.set_defaults(user_debug_gui=False)
    parser.add_argument("--execute", action="store_true", help="Actually run the Betaflight SITL workflow after a successful layout check.")
    parser.add_argument("--summary-json", default=None, help="Optional path for a JSON summary of the preflight or execution result.")
    return parser


def _enum_value(enum_cls: Any, value: str):
    return enum_cls(value)


def _write_summary(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    summary_path = Path(path).expanduser().resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.num_drones <= 0:
        raise SystemExit("--num-drones must be a positive integer")
    if args.duration_sec <= 0:
        raise SystemExit("--duration-sec must be positive")

    layout = inspect_layout(args.base_dir, args.num_drones)
    if not layout["complete"]:
        summary = {"ok": False, "mode": "check-only", "reason": "incomplete-layout", "layout": layout}
        print(json.dumps(summary, indent=2, sort_keys=True))
        _write_summary(args.summary_json, summary)
        return 1

    if not args.execute:
        summary = {"ok": True, "mode": "check-only", "layout": layout, "message": "Layout is complete. Pass --execute only if you explicitly want to launch the SITL workflow."}
        print(json.dumps(summary, indent=2, sort_keys=True))
        _write_summary(args.summary_json, summary)
        return 0

    try:
        from gym_pybullet_drones.examples.beta import run as beta_run
        from gym_pybullet_drones.utils.enums import DroneModel, Physics
    except Exception as exc:  # noqa: BLE001 - CLI boundary.
        raise SystemExit(
            "The gym-pybullet-drones package or its Betaflight example could not be imported. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    summary = {
        "ok": True,
        "mode": "execute",
        "layout": layout,
        "requested": {
            "drone": args.drone,
            "physics": args.physics,
            "num_drones": args.num_drones,
            "duration_sec": args.duration_sec,
            "output_folder": str(Path(args.output_folder).expanduser().resolve()),
            "simulation_freq_hz": args.simulation_freq_hz,
            "control_freq_hz": args.control_freq_hz,
            "gui": bool(args.gui),
            "plot": bool(args.plot),
            "user_debug_gui": bool(args.user_debug_gui),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    _write_summary(args.summary_json, summary)

    beta_run(
        drone=_enum_value(DroneModel, args.drone),
        num_drones=args.num_drones,
        physics=_enum_value(Physics, args.physics),
        gui=bool(args.gui),
        plot=bool(args.plot),
        user_debug_gui=bool(args.user_debug_gui),
        simulation_freq_hz=args.simulation_freq_hz,
        control_freq_hz=args.control_freq_hz,
        duration_sec=args.duration_sec,
        output_folder=str(Path(args.output_folder).expanduser().resolve()),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

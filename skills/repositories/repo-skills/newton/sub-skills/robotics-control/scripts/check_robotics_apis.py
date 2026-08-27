#!/usr/bin/env python3
"""Inspect public Newton robotics-control APIs and optional policy backends."""

from __future__ import annotations

import argparse
import importlib
import inspect

TARGETS = [
    ("newton.actuators", "ControllerPD"),
    ("newton.actuators", "ControllerPID"),
    ("newton.actuators", "Actuator"),
    ("newton.actuators", "Delay"),
    ("newton.controllers", "ControllerJointImpedance"),
    ("newton.controllers", "ControllerJointImpedanceModelFree"),
    ("newton.ik", "IKSolver"),
    ("newton.ik", "IKObjectivePosition"),
    ("newton.ik", "IKObjectiveRotation"),
    ("newton.ik", "IKObjectiveJointLimit"),
    ("newton.selection", "ArticulationView"),
]
OPTIONAL = {
    "warp_nn": "newton[onnx] for ONNX neural actuator/policy workflows",
    "onnx": "newton[onnx] for ONNX checkpoint parsing",
    "torch": "newton[torch-cu12] or newton[torch-cu13] for Torch checkpoints",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Newton robotics APIs and optional policy modules.")
    parser.add_argument("--optional-only", action="store_true")
    args = parser.parse_args()

    try:
        import newton
    except ModuleNotFoundError:
        print("ERROR: Newton is not importable. Install the base package first.")
        return 2

    print(f"newton={getattr(newton, '__version__', 'unknown')}")
    if not args.optional_only:
        for mod_name, attr in TARGETS:
            try:
                mod = importlib.import_module(mod_name)
                obj = getattr(mod, attr)
                print(f"{mod_name}.{attr}{inspect.signature(obj)}")
            except Exception as exc:  # noqa: BLE001
                print(f"{mod_name}.{attr}: unavailable ({type(exc).__name__}: {exc})")

    for module, extra in OPTIONAL.items():
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001
            print(f"optional.{module}=missing ({type(exc).__name__}: {exc}); install via {extra}")
        else:
            print(f"optional.{module}=available; {extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

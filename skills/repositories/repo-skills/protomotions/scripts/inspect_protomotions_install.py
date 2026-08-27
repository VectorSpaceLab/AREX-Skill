#!/usr/bin/env python3
"""Inspect an installed ProtoMotions environment without starting a simulator.

Run inside the target environment:

    python inspect_protomotions_install.py --json

The script imports safe package surfaces, queries distribution metadata, and
uses the package's own info payload when available. It does not run training,
open a viewer, download data, or require GPU access.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
from importlib import metadata
from typing import Any


def _safe_call(label: str, func):
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream):
            value = func()
        result = {"ok": True, "value": value}
    except Exception as exc:  # pragma: no cover - diagnostic path
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    captured = stream.getvalue().strip()
    if captured:
        result["captured_stdout"] = captured.splitlines()[-20:]
    return result


def collect() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version,
        "executable": sys.executable,
        "distributions": {},
        "imports": {},
        "entry_points": [],
        "protomotions_info": None,
        "smokes": {},
    }

    for dist_name in ("protomotions", "torch", "mujoco", "onnxruntime"):
        payload["distributions"][dist_name] = _safe_call(
            dist_name, lambda name=dist_name: metadata.version(name)
        )

    for module_name in (
        "protomotions",
        "protomotions.cli",
        "protomotions.assets",
        "protomotions.robot_configs.factory",
        "protomotions.simulator.factory",
        "protomotions.components.motion_lib",
    ):
        payload["imports"][module_name] = _safe_call(
            module_name, lambda name=module_name: importlib.import_module(name).__file__
        )

    payload["entry_points"] = sorted(
        ep.name
        for ep in metadata.entry_points(group="console_scripts")
        if ep.name.startswith("protomotions")
    )

    def info_payload():
        from protomotions.cli import _info_payload

        info = _info_payload()
        # Preserve booleans and version data, but callers should avoid copying
        # machine-specific roots into public docs.
        return info

    payload["protomotions_info"] = _safe_call("protomotions info", info_payload)

    def factory_smoke():
        from protomotions.components.motion_lib import MotionLibConfig
        from protomotions.robot_configs.factory import robot_config
        from protomotions.simulator.factory import get_simulator_config_class
        from protomotions.utils.simulator_imports import import_simulator_before_torch

        g1 = robot_config("g1")
        return {
            "g1_actions": g1.number_of_actions,
            "g1_num_dofs": g1.kinematic_info.num_dofs,
            "mujoco_config_class": get_simulator_config_class("mujoco").__name__,
            "empty_motion_file": MotionLibConfig().motion_file,
            "mujoco_import_order_result": str(import_simulator_before_torch("mujoco")),
        }

    payload["smokes"]["factories"] = _safe_call("factory smoke", factory_smoke)

    def torch_smoke():
        import torch

        x = torch.empty((1,), device="cpu")
        return {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "cpu_tensor_shape": list(x.shape),
        }

    payload["smokes"]["torch"] = _safe_call("torch smoke", torch_smoke)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()
    data = collect()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("ProtoMotions inspection")
        print(json.dumps(data, indent=2, sort_keys=True))
    failed = []
    for group in ("distributions", "imports"):
        failed.extend(k for k, v in data[group].items() if not v.get("ok"))
    failed.extend(k for k, v in data["smokes"].items() if not v.get("ok"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

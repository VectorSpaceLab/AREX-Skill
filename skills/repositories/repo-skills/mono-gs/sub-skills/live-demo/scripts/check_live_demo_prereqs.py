#!/usr/bin/env python3
"""Check MonoGS live-demo optional dependencies without opening the GUI."""

import argparse
import importlib
import json
import sys


def check_import(module, required=False):
    try:
        mod = importlib.import_module(module)
        return {"name": f"import {module}", "status": "pass", "detail": getattr(mod, "__version__", "imported")}
    except Exception as exc:  # noqa: BLE001
        return {"name": f"import {module}", "status": "fail" if required else "warn", "detail": f"{type(exc).__name__}: {exc}"}


def check_cuda(required=False):
    try:
        import torch
        ok = torch.cuda.is_available()
        detail = f"torch={torch.__version__}; cuda_runtime={torch.version.cuda}; available={ok}"
        if ok:
            detail += f"; device={torch.cuda.get_device_name(0)}"
        return {"name": "torch CUDA", "status": "pass" if ok else ("fail" if required else "warn"), "detail": detail}
    except Exception as exc:  # noqa: BLE001
        return {"name": "torch CUDA", "status": "fail" if required else "warn", "detail": f"{type(exc).__name__}: {exc}"}


def probe_camera(required=False):
    try:
        import pyrealsense2 as rs  # type: ignore
        ctx = rs.context()
        devices = ctx.query_devices()
        names = []
        for dev in devices:
            try:
                names.append(dev.get_info(rs.camera_info.name))
            except Exception:
                names.append("unknown-device")
        ok = len(names) > 0
        return {"name": "RealSense device query", "status": "pass" if ok else ("fail" if required else "warn"), "detail": ", ".join(names) if names else "no devices reported"}
    except Exception as exc:  # noqa: BLE001
        return {"name": "RealSense device query", "status": "fail" if required else "warn", "detail": f"{type(exc).__name__}: {exc}"}


def main():
    parser = argparse.ArgumentParser(description="Check RealSense and GUI prerequisites for MonoGS live demos.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail when CUDA is unavailable")
    parser.add_argument("--require-realsense", action="store_true", help="Fail when pyrealsense2 is unavailable")
    parser.add_argument("--probe-camera", action="store_true", help="Query attached RealSense devices; use only with user approval")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    checks = [
        check_cuda(args.require_cuda),
        check_import("open3d", required=True),
        check_import("glfw", required=True),
        check_import("OpenGL.GL", required=True),
        check_import("imgviz", required=True),
        check_import("pyrealsense2", required=args.require_realsense),
    ]
    if args.probe_camera:
        checks.append(probe_camera(required=args.require_realsense))

    failed = [c for c in checks if c["status"] == "fail"]
    if args.json:
        print(json.dumps({"ok": not failed, "checks": checks}, indent=2))
    else:
        for c in checks:
            print(f"[{c['status'].upper()}] {c['name']}: {c['detail']}")
        print("OVERALL:", "PASS" if not failed else "FAIL")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

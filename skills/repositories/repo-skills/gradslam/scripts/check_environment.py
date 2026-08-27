#!/usr/bin/env python3
"""Report GradSLAM import, dependency, and backend facts without mutation."""

from __future__ import print_function

import argparse
import importlib
import json
import platform
import sys


def _version(module):
    return getattr(module, "__version__", None) or getattr(module, "VERSION", None)


def _probe(name):
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": str(_version(module) or "unknown")}, module
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, None


def _parser():
    parser = argparse.ArgumentParser(
        description="Probe GradSLAM imports and CPU/CUDA facts without installing packages."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print one machine-readable JSON object."
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Return nonzero unless the active Torch reports CUDA available.",
    )
    return parser


def build_report():
    report = {
        "python": platform.python_version(),
        "platform": platform.system().lower(),
        "imports": {},
    }
    modules = {}
    for name in ("torch", "open3d", "chamferdist", "kornia", "cv2", "plotly", "yaml"):
        result, module = _probe(name)
        report["imports"][name] = result
        modules[name] = module

    torch = modules.get("torch")
    if torch is None:
        report["torch"] = {"cuda_available": False, "build": "unavailable"}
    else:
        report["torch"] = {
            "version": str(torch.__version__),
            "cuda_available": bool(torch.cuda.is_available()),
            "build_cuda": str(torch.version.cuda or "none"),
        }

    gradslam_result, gradslam = _probe("gradslam")
    report["imports"]["gradslam"] = gradslam_result
    if gradslam is not None:
        report["gradslam"] = {
            "version": str(getattr(gradslam, "__version__", "unknown")),
            "projective_exports": {
                name: bool(hasattr(gradslam, name))
                for name in (
                    "homogenize_points",
                    "unhomogenize_points",
                    "project_points",
                    "unproject_points",
                    "inverse_intrinsics",
                )
            },
            "structure_exports": {
                name: bool(hasattr(gradslam, name))
                for name in ("RGBDImages", "Pointclouds")
            },
        }
    return report


def main(argv=None):
    args = _parser().parse_args(argv)
    report = build_report()
    required = ("gradslam", "torch", "open3d", "chamferdist", "kornia", "cv2", "plotly", "yaml")
    failures = [name for name in required if not report["imports"][name]["ok"]]
    cuda_ok = report["torch"]["cuda_available"]
    report["status"] = "ok" if not failures and (cuda_ok or not args.require_cuda) else "failed"
    report["failed_imports"] = failures
    if args.require_cuda and not cuda_ok:
        report["cuda_requirement"] = "not satisfied"

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print("GradSLAM environment: %s" % report["status"].upper())
        print("Python %s; platform %s" % (report["python"], report["platform"]))
        for name in required:
            result = report["imports"][name]
            if result["ok"]:
                print("[ok] %s %s" % (name, result["version"]))
            else:
                print("[fail] %s: %s: %s" % (name, result["error_type"], result["error"]))
        torch = report["torch"]
        print("Torch build CUDA: %s; CUDA available: %s" % (torch.get("build_cuda"), torch["cuda_available"]))
        if args.require_cuda and not cuda_ok:
            print("[fail] --require-cuda was requested but CUDA is unavailable")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

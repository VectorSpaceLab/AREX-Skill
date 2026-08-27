#!/usr/bin/env python3
"""
Check a MonoGS runtime without starting SLAM.

This helper is safe by default: it imports modules, checks CUDA availability,
verifies optional dependencies, and prints a JSON/plain-text report. It never
runs datasets, opens a GUI window, downloads data, or modifies files.

Example:
  python check_monogs_environment.py --repo-root /path/to/MonoGS --require-cuda
"""

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def result(name, status, detail=""):
    return {"name": name, "status": status, "detail": detail}


def try_import(module):
    try:
        mod = importlib.import_module(module)
        return True, getattr(mod, "__version__", "imported")
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return False, f"{type(exc).__name__}: {exc}"


def torch_cuda_check(require_cuda):
    ok, detail = try_import("torch")
    if not ok:
        return [result("torch import", "fail", detail)]
    import torch  # type: ignore

    rows = [
        result("torch import", "pass", f"torch={torch.__version__}, cuda_runtime={torch.version.cuda}"),
        result("torch.cuda.is_available", "pass" if torch.cuda.is_available() else ("fail" if require_cuda else "warn"), str(torch.cuda.is_available())),
    ]
    if torch.cuda.is_available():
        try:
            x = torch.empty((1,), device="cuda")
            rows.append(result("cuda tensor allocation", "pass", f"device={x.device}; gpu={torch.cuda.get_device_name(0)}; capability={torch.cuda.get_device_capability(0)}"))
        except Exception as exc:  # noqa: BLE001
            rows.append(result("cuda tensor allocation", "fail", f"{type(exc).__name__}: {exc}"))
    return rows


def nvcc_check(require_cuda):
    nvcc = shutil.which("nvcc")
    if not nvcc:
        return result("nvcc", "fail" if require_cuda else "warn", "nvcc not found on PATH; extension builds need CUDA toolkit/compiler")
    try:
        proc = subprocess.run([nvcc, "--version"], check=False, text=True, capture_output=True, timeout=20)
        text = (proc.stdout or proc.stderr).strip().splitlines()[-1] if (proc.stdout or proc.stderr).strip() else nvcc
        return result("nvcc", "pass" if proc.returncode == 0 else "warn", text)
    except Exception as exc:  # noqa: BLE001
        return result("nvcc", "warn", f"{type(exc).__name__}: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Check MonoGS Python, CUDA, extension, and optional GUI/RealSense dependencies.")
    parser.add_argument("--repo-root", type=Path, help="MonoGS checkout root to add to sys.path for repo module imports.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail when CUDA is unavailable. Use this for offline SLAM/evaluation readiness.")
    parser.add_argument("--require-realsense", action="store_true", help="Fail when pyrealsense2 is unavailable.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    checks = []
    checks.append(result("python", "pass", sys.version.split()[0]))

    if args.repo_root:
        root = args.repo_root.resolve()
        if not (root / "slam.py").exists():
            checks.append(result("repo root", "fail", "repo root does not contain slam.py"))
        else:
            sys.path.insert(0, str(root))
            checks.append(result("repo root", "pass", "contains slam.py"))

    checks.extend(torch_cuda_check(args.require_cuda))
    checks.append(nvcc_check(args.require_cuda))

    required_modules = [
        "yaml",
        "cv2",
        "numpy",
        "trimesh",
        "open3d",
        "wandb",
        "evo",
        "torchmetrics",
        "simple_knn._C",
        "diff_gaussian_rasterization",
    ]
    repo_modules = [
        "gaussian_splatting.gaussian_renderer",
        "gaussian_splatting.scene.gaussian_model",
        "utils.config_utils",
        "utils.dataset",
        "utils.eval_utils",
        "slam",
    ]
    optional_modules = ["glfw", "OpenGL.GL", "imgviz", "glm"]

    for module in required_modules + (repo_modules if args.repo_root else []):
        ok, detail = try_import(module)
        checks.append(result(f"import {module}", "pass" if ok else "fail", str(detail)))

    for module in optional_modules:
        ok, detail = try_import(module)
        checks.append(result(f"optional import {module}", "pass" if ok else "warn", str(detail)))

    ok, detail = try_import("pyrealsense2")
    checks.append(result("optional import pyrealsense2", "pass" if ok else ("fail" if args.require_realsense else "warn"), str(detail)))

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

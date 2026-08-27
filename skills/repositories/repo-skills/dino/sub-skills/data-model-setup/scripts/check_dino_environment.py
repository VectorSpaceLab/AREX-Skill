#!/usr/bin/env python3
"""Read-only checks for a DINO Python/CUDA environment.

This script never installs packages, builds extensions, changes environment
variables, reserves a GPU, or edits repository/data files. Use --fixture for a
self-contained check of the report/exit machinery when DINO dependencies are
not installed.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


BASE_PACKAGES = ("torch", "torchvision")
COCO_PACKAGES = ("pycocotools.mask",)
PANOPTIC_PACKAGES = ("panopticapi.utils",)
RUNTIME_PACKAGES = ("Cython", "submitit", "scipy", "termcolor", "addict", "yapf", "timm")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Read-only DINO package, PyTorch/CUDA, and optional "
            "MultiScaleDeformableAttention checks."
        )
    )
    p.add_argument("--require-cuda", action="store_true", help="fail unless CUDA is available")
    p.add_argument("--require-extension", action="store_true", help="fail unless the custom op imports")
    p.add_argument("--require-coco", action="store_true", help="require pycocotools.mask to import")
    p.add_argument("--require-runtime", action="store_true", help="require the non-COCO packages listed in requirements.txt")
    p.add_argument("--require-panoptic", action="store_true", help="require panopticapi to import")
    p.add_argument("--pip-check", action="store_true", help="run read-only 'python -m pip check'")
    p.add_argument("--smoke-cuda", action="store_true", help="allocate a tiny CUDA tensor (requires a free visible GPU)")
    p.add_argument("--smoke-extension", action="store_true", help="run a tiny custom-op CUDA forward (requires a free visible GPU)")
    p.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON report")
    p.add_argument("--fixture", action="store_true", help="run a dependency-free report fixture and exit")
    return p


def result(status: str, detail: str, required: bool = False) -> Dict[str, Any]:
    return {"status": status, "required": required, "detail": detail}


def check_import(name: str, required: bool) -> Dict[str, Any]:
    try:
        importlib.import_module(name)
    except Exception as exc:  # import errors often have useful type names
        return result("fail" if required else "warn", f"{type(exc).__name__}: {exc}", required)
    return result("pass", "imported", required)


def check_torch(require_cuda: bool, smoke_cuda: bool) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        failed = result("fail", f"{type(exc).__name__}: {exc}", True)
        return failed, result("skip", "torch import failed", require_cuda or smoke_cuda)

    version = getattr(torch, "__version__", "unknown")
    cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
    available = bool(torch.cuda.is_available())
    detail = f"torch {version}; torch CUDA {cuda_version or 'none'}; cuda_available={available}"
    torch_result = result("pass", detail, True)
    if require_cuda and not available:
        torch_result = result("fail", detail, True)

    if not (require_cuda or smoke_cuda):
        return torch_result, result("skip", "CUDA smoke not requested", False)
    if not available:
        return torch_result, result("fail" if smoke_cuda else "skip", "CUDA is unavailable", require_cuda or smoke_cuda)

    try:
        device_count = int(torch.cuda.device_count())
        if device_count < 1:
            raise RuntimeError("no visible CUDA devices")
        device = torch.cuda.current_device()
        capability = torch.cuda.get_device_capability(device)
        # A 2x2 allocation is intentionally tiny; it is still sensitive to an
        # occupied/broken CUDA context and therefore is not a free-memory test.
        if smoke_cuda:
            x = torch.zeros((2, 2), device="cuda")
            _ = float(x.sum().item())
            del x
            smoke = result("pass", f"allocated on visible device {device}; capability {capability[0]}.{capability[1]}", True)
        else:
            smoke = result("pass", f"{device_count} visible device(s); capability {capability[0]}.{capability[1]}", False)
    except Exception as exc:
        smoke = result("fail" if smoke_cuda else "warn", f"{type(exc).__name__}: {exc}", smoke_cuda)
    return torch_result, smoke


def check_cuda_home() -> Dict[str, Any]:
    try:
        from torch.utils.cpp_extension import CUDA_HOME  # type: ignore
    except Exception as exc:
        return result("warn", f"cannot query PyTorch CUDA_HOME: {type(exc).__name__}: {exc}", False)
    nvcc = shutil.which("nvcc")
    if CUDA_HOME and nvcc:
        return result("pass", "PyTorch CUDA_HOME and nvcc are available", False)
    missing = []
    if not CUDA_HOME:
        missing.append("CUDA_HOME")
    if not nvcc:
        missing.append("nvcc on PATH")
    return result("warn", "missing " + " and ".join(missing), False)


def check_extension(required: bool, smoke: bool = False) -> Dict[str, Any]:
    try:
        module = importlib.import_module("MultiScaleDeformableAttention")
    except Exception as exc:
        return result("fail" if required else "warn", f"{type(exc).__name__}: {exc}", required)
    names = ("ms_deform_attn_forward", "ms_deform_attn_backward")
    missing = [name for name in names if not hasattr(module, name)]
    if missing:
        return result("fail" if required else "warn", "missing symbols: " + ", ".join(missing), required)
    if not smoke:
        return result("pass", "imported with forward/backward symbols", required)

    try:
        torch = importlib.import_module("torch")
        if not torch.cuda.is_available():
            return result("fail", "extension smoke requested but CUDA is unavailable", True)
        with torch.no_grad():
            value = torch.arange(4, dtype=torch.float32, device="cuda").reshape(1, 4, 1, 1)
            spatial_shapes = torch.tensor([[2, 2]], dtype=torch.long, device="cuda")
            level_start_index = torch.tensor([0], dtype=torch.long, device="cuda")
            sampling_locations = torch.full(
                (1, 1, 1, 1, 2, 2), 0.5, dtype=torch.float32, device="cuda"
            )
            attention_weights = torch.full(
                (1, 1, 1, 1, 2), 0.5, dtype=torch.float32, device="cuda"
            )
            output = module.ms_deform_attn_forward(
                value, spatial_shapes, level_start_index,
                sampling_locations, attention_weights, 1
            )
            if tuple(output.shape) != (1, 1, 1):
                raise RuntimeError("unexpected output shape {}".format(tuple(output.shape)))
            if not bool(torch.isfinite(output).all().item()):
                raise RuntimeError("extension smoke produced non-finite output")
    except Exception as exc:
        return result("fail", f"{type(exc).__name__}: {exc}", True)
    return result("pass", "imported and completed tiny CUDA forward", True)


def check_pip() -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    except Exception as exc:
        return result("fail", f"pip check could not run: {type(exc).__name__}: {exc}", True)
    if proc.returncode == 0:
        return result("pass", "No broken requirements found", True)
    # Do not copy arbitrary command output into reports; it may contain local
    # paths. The exit code and a bounded count are enough for routing.
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return result("fail", f"pip check reported {len(lines)} issue(s)", True)


def fixture_report() -> Dict[str, Any]:
    checks = {"fixture": result("pass", "dependency-free report fixture", True)}
    report = {"status": "ok", "python": f"{sys.version_info.major}.{sys.version_info.minor}", "checks": checks}
    validate_report(report)
    return report


def validate_report(report: Dict[str, Any]) -> None:
    if report.get("status") not in {"ok", "failed"}:
        raise AssertionError("invalid report status")
    checks = report.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise AssertionError("report has no checks")
    for name, check in checks.items():
        if not isinstance(name, str) or not isinstance(check, dict):
            raise AssertionError("invalid check entry")
        if check.get("status") not in {"pass", "fail", "warn", "skip"}:
            raise AssertionError(f"invalid status for {name}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parser().parse_args(argv)
    if args.fixture:
        report = fixture_report()
        print(json.dumps(report, indent=2, sort_keys=True) if args.as_json else "fixture: PASS")
        return 0

    checks: Dict[str, Dict[str, Any]] = {}
    for package in BASE_PACKAGES:
        checks[package] = check_import(package, True)
    if args.require_coco:
        checks["pycocotools"] = check_import("pycocotools.mask", True)
    if args.require_panoptic:
        checks["panopticapi"] = check_import("panopticapi.utils", True)
    for package in RUNTIME_PACKAGES:
        if args.require_runtime:
            checks[package] = check_import(package, True)

    torch_check, cuda_check = check_torch(args.require_cuda, args.smoke_cuda)
    # The torch import check above is intentionally replaced by a richer check.
    checks["torch"] = torch_check
    checks["cuda"] = cuda_check
    checks["cuda_toolkit"] = check_cuda_home()
    if args.require_extension or args.smoke_extension:
        checks["MultiScaleDeformableAttention"] = check_extension(
            True, smoke=args.smoke_extension
        )
    if args.pip_check:
        checks["pip_check"] = check_pip()

    failed = any(item["status"] == "fail" and item.get("required", False) for item in checks.values())
    report = {
        "status": "failed" if failed else "ok",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": checks,
        "notes": [
            "This report is read-only; an import is not a numerical extension test.",
            "A CUDA smoke can fail when the visible GPU is occupied; choose a free device for backend verification.",
        ],
    }
    validate_report(report)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, item in checks.items():
            print(f"{name}: {item['status'].upper()} - {item['detail']}")
        print("overall: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

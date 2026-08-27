#!/usr/bin/env python3
"""Safe XTuner backend diagnostic.

This script is intentionally import/probe-only. It does not read an XTuner source
checkout, launch training, initialize distributed process groups, or run CUDA/NPU
kernels. It reports what the current Python environment can see.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import importlib.util
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from typing import Any


CORE_OPTIONAL_IMPORTS = [
    ("flash_attn", "flash-attn"),
    ("flash_attn_interface", None),
    ("bitsandbytes", "bitsandbytes"),
    ("ray", "ray"),
]

EXTENDED_OPTIONAL_IMPORTS = [
    ("triton", "triton"),
    ("grouped_gemm", "grouped_gemm"),
    ("adaptive_gemm", "adaptive_gemm"),
    ("deep_ep", "deep_ep"),
    ("deep_ep_cpp", "deep_ep_cpp"),
    ("torch_npu", "torch-npu"),
]

XTUNER_IMPORTS = [
    "xtuner",
    "xtuner.v1.config",
    "xtuner.v1.float8.config",
    "xtuner.v1.module.router.greedy",
    "xtuner.v1.module.attention",
    "xtuner.v1.model",
]


def _status(ok: bool, detail: str | None = None) -> str:
    if ok:
        return "ok"
    if detail:
        return "missing" if "No module named" in detail or "not found" in detail else "error"
    return "error"


def _dist_version(dist_name: str | None, module: Any | None = None) -> str | None:
    names = []
    if dist_name:
        names.append(dist_name)
    if module is not None:
        mod_name = getattr(module, "__name__", None)
        if mod_name:
            names.append(mod_name.replace("_", "-"))
            names.append(mod_name)
    for name in names:
        try:
            return metadata.version(name)
        except Exception:
            pass
    if module is not None:
        version = getattr(module, "__version__", None)
        if isinstance(version, str):
            return version
    return None


def probe_import(module_name: str, dist_name: str | None = None, do_import: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {"module": module_name, "status": "unknown"}
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:
        spec = None
        result["find_spec_error"] = f"{type(exc).__name__}: {exc}"

    result["found"] = spec is not None
    if spec is not None:
        result["origin"] = getattr(spec, "origin", None)

    if not do_import:
        result["status"] = "found" if spec is not None else "missing"
        return result

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            module = importlib.import_module(module_name)
    except Exception as exc:
        result["status"] = _status(False, str(exc))
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback_tail"] = traceback.format_exc(limit=2).strip().splitlines()[-6:]
    else:
        result["status"] = "ok"
        result["version"] = _dist_version(dist_name, module)
        result["file"] = getattr(module, "__file__", None)
    finally:
        out = stdout_buf.getvalue().strip()
        err = stderr_buf.getvalue().strip()
        if out:
            result["stdout"] = out[-4000:]
        if err:
            result["stderr"] = err[-4000:]
    return result


def probe_torch() -> dict[str, Any]:
    result: dict[str, Any] = {"status": "unknown"}
    try:
        import torch
    except Exception as exc:
        result.update(
            {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback_tail": traceback.format_exc(limit=2).strip().splitlines()[-6:],
            }
        )
        return result

    result["status"] = "ok"
    result["version"] = getattr(torch, "__version__", None)
    result["file"] = getattr(torch, "__file__", None)
    result["cuda_build"] = getattr(getattr(torch, "version", None), "cuda", None)
    result["hip_build"] = getattr(getattr(torch, "version", None), "hip", None)
    result["has_float8_e4m3fn"] = hasattr(torch, "float8_e4m3fn")

    cuda_info: dict[str, Any] = {}
    try:
        cuda_info["available"] = bool(torch.cuda.is_available())
        cuda_info["device_count"] = int(torch.cuda.device_count()) if cuda_info["available"] else 0
        devices = []
        for idx in range(cuda_info["device_count"]):
            props = torch.cuda.get_device_properties(idx)
            capability = torch.cuda.get_device_capability(idx)
            devices.append(
                {
                    "index": idx,
                    "name": torch.cuda.get_device_name(idx),
                    "capability": list(capability),
                    "total_memory_gib": round(props.total_memory / (1024**3), 2),
                }
            )
        cuda_info["devices"] = devices
        cuda_info["any_sm89_or_later"] = any(tuple(d["capability"]) >= (8, 9) for d in devices)
    except Exception as exc:
        cuda_info["error"] = f"{type(exc).__name__}: {exc}"
    result["cuda"] = cuda_info
    return result


def probe_nvidia_smi() -> dict[str, Any]:
    exe = shutil.which("nvidia-smi")
    result: dict[str, Any] = {"found": exe is not None}
    if exe is None:
        result["status"] = "missing"
        return result
    try:
        completed = subprocess.run(
            [exe, "--query-gpu=name,driver_version,cuda_version", "--format=csv,noheader"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        return result
    result["status"] = "ok" if completed.returncode == 0 else "error"
    result["returncode"] = completed.returncode
    if completed.stdout.strip():
        result["stdout"] = completed.stdout.strip().splitlines()
    if completed.stderr.strip():
        result["stderr"] = completed.stderr.strip()[-2000:]
    return result


def probe_xtuner_imports() -> dict[str, Any]:
    result: dict[str, Any] = {"imports": {}, "config_smoke": {}}
    for module_name in XTUNER_IMPORTS:
        result["imports"][module_name] = probe_import(module_name, do_import=True)

    smoke: dict[str, Any] = {}
    try:
        from xtuner.v1.config import FSDPConfig

        cfg = FSDPConfig()
        smoke["FSDPConfig"] = {"status": "ok", "fields": list(type(cfg).model_fields)}
    except Exception as exc:
        smoke["FSDPConfig"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    try:
        from xtuner.v1.float8.config import Float8Config, ScalingGranularity

        cfg = Float8Config(scaling_granularity_gemm=ScalingGranularity.TILEWISE)
        smoke["Float8Config"] = {"status": "ok", "enable_float8": bool(cfg.enable_float8)}
    except Exception as exc:
        smoke["Float8Config"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    try:
        from xtuner.v1.model import get_model_config

        aliases = ["qwen3-8B", "qwen3-moe-30BA3", "intern-s1-mini"]
        resolved = {}
        for alias in aliases:
            cfg = get_model_config(alias)
            resolved[alias] = type(cfg).__name__ if cfg is not None else None
        smoke["get_model_config"] = {"status": "ok", "aliases": resolved}
    except Exception as exc:
        smoke["get_model_config"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    result["config_smoke"] = smoke
    return result


def build_assessments(report: dict[str, Any]) -> list[str]:
    assessments: list[str] = []
    torch_info = report.get("torch", {})
    cuda = torch_info.get("cuda", {}) if isinstance(torch_info, dict) else {}

    if torch_info.get("status") != "ok":
        assessments.append("Torch import failed; no XTuner backend claim is possible.")
        return assessments

    if not cuda.get("available"):
        assessments.append("CUDA is not visible to Torch; results are CPU/import-level only.")
    else:
        count = cuda.get("device_count", 0)
        assessments.append(f"Torch sees CUDA with {count} device(s); optional CUDA extensions still need separate checks.")
        if cuda.get("any_sm89_or_later"):
            assessments.append("At least one CUDA device reports SM89 or later; FP8 hardware capability is plausible, not yet kernel-verified.")
        else:
            assessments.append("No visible CUDA device reports SM89 or later; XTuner FP8 acceleration is unverified or unavailable.")

    optional = report.get("optional_imports", {})
    flash = optional.get("flash_attn", {})
    flash3 = optional.get("flash_attn_interface", {})
    if flash.get("status") != "ok" and flash3.get("status") != "ok":
        assessments.append("FlashAttention imports are missing or failing; expect XTuner flash-attention paths to fall back or remain unverified.")

    bnb = optional.get("bitsandbytes", {})
    bnb_text = "\n".join(str(bnb.get(k, "")) for k in ("stdout", "stderr", "error"))
    cuda_build = str(torch_info.get("cuda_build") or "")
    if bnb.get("status") != "ok":
        assessments.append("bitsandbytes did not import cleanly; do not rely on BNB GPU features.")
    elif "without GPU support" in bnb_text or "Could not find" in bnb_text:
        assessments.append("bitsandbytes imported with GPU-support warnings; BNB GPU quantization/8-bit paths are not verified.")
    if cuda_build.startswith("13") and bnb.get("status") == "ok" and ("cuda13" in bnb_text.lower() or "cuda 13" in bnb_text.lower() or "Could not find" in bnb_text):
        assessments.append("The active Torch CUDA build appears to be CUDA 13 and bitsandbytes reported binary warnings; use a matching BNB build or avoid BNB GPU paths.")

    grouped = optional.get("grouped_gemm", {})
    if grouped and grouped.get("status") != "ok":
        assessments.append("grouped_gemm is unavailable; fused CUTLASS/grouped_gemm paths are unverified.")

    adaptive = optional.get("adaptive_gemm", {})
    if adaptive and adaptive.get("status") != "ok":
        assessments.append("adaptive_gemm is unavailable; tile-wise XTuner FP8 linear/grouped-linear acceleration is unverified.")

    deep_ep = optional.get("deep_ep", {})
    deep_ep_cpp = optional.get("deep_ep_cpp", {})
    if deep_ep and (deep_ep.get("status") != "ok" or deep_ep_cpp.get("status") != "ok"):
        assessments.append("DeepEP imports are incomplete; do not select dispatcher='deepep' without installing and verifying DeepEP.")

    npu = optional.get("torch_npu", {})
    if npu and npu.get("status") != "ok":
        assessments.append("torch_npu is unavailable; NPU backend support is unverified.")

    xtuner = report.get("xtuner", {})
    smoke = xtuner.get("config_smoke", {}) if isinstance(xtuner, dict) else {}
    failed_smoke = [name for name, item in smoke.items() if isinstance(item, dict) and item.get("status") != "ok"]
    if failed_smoke:
        assessments.append("Selected XTuner config smoke checks failed: " + ", ".join(failed_smoke))
    elif smoke:
        assessments.append("Selected XTuner config imports/smoke checks passed; this is not a training or kernel verification.")

    return assessments


def make_report(args: argparse.Namespace) -> dict[str, Any]:
    optional_imports = list(CORE_OPTIONAL_IMPORTS)
    if args.check_optional:
        optional_imports.extend(EXTENDED_OPTIONAL_IMPORTS)

    report: dict[str, Any] = {
        "script": "check_xtuner_backend.py",
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "environment": {
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "CUDA_HOME": os.environ.get("CUDA_HOME"),
            "XTUNER_USE_FA3": os.environ.get("XTUNER_USE_FA3"),
            "XTUNER_HF_IMPL": os.environ.get("XTUNER_HF_IMPL"),
        },
    }
    report["torch"] = probe_torch()
    if not args.skip_nvidia_smi:
        report["nvidia_smi"] = probe_nvidia_smi()
    report["optional_imports"] = {name: probe_import(name, dist_name=dist) for name, dist in optional_imports}
    if not args.skip_xtuner_imports:
        report["xtuner"] = probe_xtuner_imports()
    report["assessments"] = build_assessments(report)
    return report


def print_human(report: dict[str, Any]) -> None:
    print("XTuner backend diagnostic (safe import/probe only)")
    print("=" * 58)
    py = report["python"]
    print(f"Python: {py['version']} ({py['executable']})")
    print(f"Platform: {py['platform']}")

    torch_info = report.get("torch", {})
    print("\nTorch")
    print("-----")
    if torch_info.get("status") != "ok":
        print(f"status: {torch_info.get('status')} {torch_info.get('error', '')}")
    else:
        print(f"version: {torch_info.get('version')}")
        print(f"cuda build: {torch_info.get('cuda_build')}")
        cuda = torch_info.get("cuda", {})
        print(f"cuda available: {cuda.get('available')} (device_count={cuda.get('device_count')})")
        for dev in cuda.get("devices", []) or []:
            print(
                "  - cuda:{index} {name} sm={capability} memory={total_memory_gib} GiB".format(
                    **dev
                )
            )
        print(f"has torch.float8_e4m3fn: {torch_info.get('has_float8_e4m3fn')}")

    print("\nOptional imports")
    print("----------------")
    for name, item in sorted(report.get("optional_imports", {}).items()):
        version = f" version={item.get('version')}" if item.get("version") else ""
        print(f"{name}: {item.get('status')}{version}")
        detail = item.get("error") or item.get("stderr") or item.get("stdout")
        if detail:
            first_line = str(detail).strip().splitlines()[0]
            print(f"  detail: {first_line[:180]}")

    if "xtuner" in report:
        print("\nSelected XTuner imports")
        print("-----------------------")
        xtuner = report.get("xtuner", {})
        for name, item in sorted((xtuner.get("imports") or {}).items()):
            print(f"{name}: {item.get('status')}")
            detail = item.get("error") or item.get("stderr") or item.get("stdout")
            if detail:
                first_line = str(detail).strip().splitlines()[0]
                print(f"  detail: {first_line[:180]}")
        print("\nXTuner config smoke")
        for name, item in sorted((xtuner.get("config_smoke") or {}).items()):
            print(f"{name}: {item.get('status')}")
            if "aliases" in item:
                print(f"  aliases: {item['aliases']}")
            if "error" in item:
                print(f"  error: {item['error']}")

    print("\nAssessments")
    print("-----------")
    for assessment in report.get("assessments", []):
        print(f"- {assessment}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe XTuner backend diagnostic; no training or kernel execution.")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    parser.add_argument("--check-optional", action="store_true", help="also probe extended optional deps: triton, grouped_gemm, adaptive_gemm, DeepEP, torch_npu")
    parser.add_argument("--expect-cuda", action="store_true", help="exit nonzero if Torch cannot see CUDA")
    parser.add_argument("--strict", action="store_true", help="exit nonzero if selected XTuner config smoke checks fail")
    parser.add_argument("--skip-xtuner-imports", action="store_true", help="skip XTuner import/config smoke checks")
    parser.add_argument("--skip-nvidia-smi", action="store_true", help="skip nvidia-smi probe")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.json:
        # Some optional packages and XTuner loggers write directly to stdout/stderr
        # during import. Capture generation noise so JSON mode remains parseable.
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            report = make_report(args)
        captured_stdout = stdout_buf.getvalue().strip()
        captured_stderr = stderr_buf.getvalue().strip()
        if captured_stdout or captured_stderr:
            report["captured_output"] = {}
            if captured_stdout:
                report["captured_output"]["stdout"] = captured_stdout[-4000:]
            if captured_stderr:
                report["captured_output"]["stderr"] = captured_stderr[-4000:]
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        report = make_report(args)
        print_human(report)

    exit_code = 0
    cuda = ((report.get("torch") or {}).get("cuda") or {}) if isinstance(report.get("torch"), dict) else {}
    if args.expect_cuda and not cuda.get("available"):
        exit_code = max(exit_code, 2)
    if args.strict and not args.skip_xtuner_imports:
        smoke = (((report.get("xtuner") or {}).get("config_smoke") or {})) if isinstance(report.get("xtuner"), dict) else {}
        if any(isinstance(item, dict) and item.get("status") != "ok" for item in smoke.values()):
            exit_code = max(exit_code, 3)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

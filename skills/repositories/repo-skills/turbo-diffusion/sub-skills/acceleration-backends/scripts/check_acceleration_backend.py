#!/usr/bin/env python3
"""Safe TurboDiffusion acceleration backend diagnostic.

This script imports packages and runs tiny CUDA custom-op/FastNorm checks when
CUDA is available. It does not download checkpoints, run inference, train, read
credentials, or depend on a repository checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import shutil
import sys
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Check:
    name: str
    status: str
    required: bool = False
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def import_module(name: str):
    return importlib.import_module(name)


def module_spec_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def add(checks: list[Check], name: str, status: str, required: bool = False, detail: str = "", **data: Any) -> None:
    checks.append(Check(name=name, status=status, required=required, detail=detail, data={k: v for k, v in data.items() if v is not None}))


def finite_tensor(torch_mod, tensor) -> bool:
    try:
        return bool(torch_mod.isfinite(tensor).all().item())
    except Exception:
        return False


def run_cuda_smokes(checks: list[Check], torch_mod, ops_mod, device_index: int) -> None:
    device = torch_mod.device(f"cuda:{device_index}")
    torch_mod.cuda.set_device(device)

    # Tiny quantization smoke. Shape multiples of 128 match the block-scale path.
    try:
        x = torch_mod.randn((2, 128), device=device, dtype=torch_mod.float16).contiguous()
        x_q, scale = ops_mod.int8_quant(x)
        ok = x_q.dtype == torch_mod.int8 and finite_tensor(torch_mod, scale.float())
        add(
            checks,
            "int8_quant tiny CUDA smoke",
            "pass" if ok else "fail",
            required=True,
            detail="quantized a 2x128 fp16 tensor" if ok else "unexpected dtype or non-finite scale",
            quant_dtype=str(x_q.dtype),
            scale_shape=list(scale.shape),
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        add(checks, "int8_quant tiny CUDA smoke", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")

    try:
        linear = torch_mod.nn.Linear(128, 128, bias=True, dtype=torch_mod.float16).to(device).eval()
        qlinear = ops_mod.Int8Linear.from_linear(linear, quantize=True).to(device).eval()
        x = torch_mod.randn((2, 128), device=device, dtype=torch_mod.float16).contiguous()
        with torch_mod.no_grad():
            y = qlinear(x)
        ok = list(y.shape) == [2, 128] and finite_tensor(torch_mod, y.float())
        add(
            checks,
            "Int8Linear tiny CUDA smoke",
            "pass" if ok else "fail",
            required=True,
            detail="ran Int8Linear.from_linear on a 128x128 layer" if ok else "unexpected shape or non-finite output",
            output_shape=list(y.shape),
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        add(checks, "Int8Linear tiny CUDA smoke", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")

    try:
        rms = ops_mod.FastRMSNorm(16).to(device).eval()
        x = torch_mod.randn((2, 16), device=device, dtype=torch_mod.float16).contiguous()
        with torch_mod.no_grad():
            y = rms(x)
        ok = list(y.shape) == [2, 16] and finite_tensor(torch_mod, y.float())
        add(
            checks,
            "FastRMSNorm tiny CUDA smoke",
            "pass" if ok else "fail",
            required=True,
            detail="ran FastRMSNorm on a 2x16 tensor" if ok else "unexpected shape or non-finite output",
            output_shape=list(y.shape),
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        add(checks, "FastRMSNorm tiny CUDA smoke", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")

    try:
        base_ln = torch_mod.nn.LayerNorm(16).to(device).eval()
        fast_ln = ops_mod.FastLayerNorm.from_layernorm(base_ln).to(device).eval()
        x = torch_mod.randn((2, 16), device=device, dtype=torch_mod.float16).contiguous()
        with torch_mod.no_grad():
            y = fast_ln(x)
        ok = list(y.shape) == [2, 16] and finite_tensor(torch_mod, y.float())
        add(
            checks,
            "FastLayerNorm tiny CUDA smoke",
            "pass" if ok else "fail",
            required=True,
            detail="ran FastLayerNorm.from_layernorm on a 2x16 tensor" if ok else "unexpected shape or non-finite output",
            output_shape=list(y.shape),
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        add(checks, "FastLayerNorm tiny CUDA smoke", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")


def run_optional_sla_smoke(checks: list[Check], torch_mod, sla_core, device_index: int) -> None:
    device = torch_mod.device(f"cuda:{device_index}")
    torch_mod.cuda.set_device(device)
    try:
        module = sla_core.SparseLinearAttention(head_dim=64, topk=0.1).to(device).eval()
        q = torch_mod.randn((1, 2, 128, 64), device=device, dtype=torch_mod.float16)
        k = torch_mod.randn((1, 2, 128, 64), device=device, dtype=torch_mod.float16)
        v = torch_mod.randn((1, 2, 128, 64), device=device, dtype=torch_mod.float16)
        with torch_mod.no_grad():
            out = module(q, k, v)
        ok = list(out.shape) == [1, 2, 128, 64] and finite_tensor(torch_mod, out.float())
        add(
            checks,
            "SparseLinearAttention optional tiny random forward",
            "pass" if ok else "warn",
            required=False,
            detail=(
                "tiny random forward produced finite output"
                if ok
                else "tiny random forward produced non-finite output; use only as a warning, not a model correctness signal"
            ),
            output_shape=list(out.shape),
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        add(
            checks,
            "SparseLinearAttention optional tiny random forward",
            "warn",
            required=False,
            detail=f"{type(exc).__name__}: {exc}",
        )


def render_text(checks: list[Check], summary: dict[str, Any]) -> str:
    lines = ["TurboDiffusion acceleration backend diagnostic", ""]
    lines.append(f"overall: {summary['overall']}")
    lines.append(f"python: {summary['python']}")
    lines.append(f"platform: {summary['platform']}")
    lines.append("")
    for check in checks:
        req = " required" if check.required else ""
        lines.append(f"[{check.status.upper()}]{req} {check.name}")
        if check.detail:
            lines.append(f"  {check.detail}")
        if check.data:
            for key, value in check.data.items():
                lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose TurboDiffusion CUDA/custom-op/SLA backend readiness without model downloads or inference."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit non-zero if CUDA is unavailable.")
    parser.add_argument("--require-sagesla", action="store_true", help="Exit non-zero if SpargeAttn/SageSLA is unavailable.")
    parser.add_argument(
        "--sla-forward-smoke",
        action="store_true",
        help="Optionally run a tiny random SparseLinearAttention forward. This may JIT kernels and is warning-only.",
    )
    parser.add_argument("--device", type=int, default=0, help="CUDA device index for tiny CUDA smokes. Default: 0.")
    parser.add_argument("--show-traceback", action="store_true", help="Include tracebacks for unexpected diagnostic failures.")
    args = parser.parse_args(argv)

    checks: list[Check] = []
    torch_mod = None
    ops_mod = None
    sla_core = None

    try:
        torch_mod = import_module("torch")
        add(
            checks,
            "torch import",
            "pass",
            required=True,
            version=getattr(torch_mod, "__version__", "unknown"),
            cuda_runtime=getattr(getattr(torch_mod, "version", None), "cuda", None),
        )
    except Exception as exc:
        add(checks, "torch import", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")

    if torch_mod is not None:
        try:
            cuda_available = bool(torch_mod.cuda.is_available())
            count = int(torch_mod.cuda.device_count()) if cuda_available else 0
            data: dict[str, Any] = {
                "available": cuda_available,
                "device_count": count,
                "nvcc_on_path": bool(shutil.which("nvcc")),
                "cuda_home_set": bool(os.environ.get("CUDA_HOME")),
            }
            if cuda_available and count > 0:
                idx = min(max(args.device, 0), count - 1)
                props = torch_mod.cuda.get_device_properties(idx)
                data.update(
                    {
                        "selected_device": idx,
                        "device_name": props.name,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "total_memory_gib": round(props.total_memory / (1024 ** 3), 2),
                    }
                )
            add(
                checks,
                "CUDA availability",
                "pass" if cuda_available else ("fail" if args.require_cuda else "skip"),
                required=args.require_cuda,
                detail="CUDA is available" if cuda_available else "CUDA unavailable; custom-op runtime smokes skipped",
                **data,
            )
        except Exception as exc:
            add(checks, "CUDA availability", "fail", required=args.require_cuda, detail=f"{type(exc).__name__}: {exc}")

    for mod_name in ["turbodiffusion", "turbo_diffusion_ops"]:
        try:
            mod = import_module(mod_name)
            symbols = []
            if mod_name == "turbo_diffusion_ops":
                symbols = [name for name in ["quant_cuda", "gemm_cuda", "rmsnorm_cuda", "layernorm_cuda"] if hasattr(mod, name)]
            add(
                checks,
                f"{mod_name} import",
                "pass",
                required=True,
                version=getattr(mod, "__version__", None),
                symbols=symbols or None,
            )
        except Exception as exc:
            add(checks, f"{mod_name} import", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")
            if args.show_traceback:
                add(checks, f"{mod_name} traceback", "warn", detail=traceback.format_exc())

    try:
        ops_mod = import_module("turbodiffusion.ops")
        expected = ["Int8Linear", "FastRMSNorm", "FastLayerNorm", "int8_quant", "int8_linear"]
        missing = [name for name in expected if not hasattr(ops_mod, name)]
        add(
            checks,
            "turbodiffusion.ops import",
            "pass" if not missing else "fail",
            required=True,
            detail="all expected symbols present" if not missing else f"missing symbols: {', '.join(missing)}",
        )
    except Exception as exc:
        add(checks, "turbodiffusion.ops import", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")
        if args.show_traceback:
            add(checks, "turbodiffusion.ops traceback", "warn", detail=traceback.format_exc())

    try:
        sla_core = import_module("turbodiffusion.SLA.core")
        sagesla_enabled = bool(getattr(sla_core, "SAGESLA_ENABLED", False))
        sage2pp_enabled = bool(getattr(sla_core, "SAGE2PP_ENABLED", False))
        add(
            checks,
            "turbodiffusion.SLA.core import",
            "pass",
            required=False,
            SAGESLA_ENABLED=sagesla_enabled,
            SAGE2PP_ENABLED=sage2pp_enabled,
        )
        add(
            checks,
            "SpargeAttn/SageSLA optional dependency",
            "pass" if sagesla_enabled else ("fail" if args.require_sagesla else "warn"),
            required=args.require_sagesla,
            detail="SageSLA is enabled" if sagesla_enabled else "SageSLA is disabled; install SpargeAttn or avoid attention_type=sagesla",
            spas_sage_attn=module_spec_exists("spas_sage_attn"),
            spas_sage_attn_qattn=module_spec_exists("spas_sage_attn._qattn"),
            spas_sage_attn_fused=module_spec_exists("spas_sage_attn._fused"),
        )
    except Exception as exc:
        add(checks, "turbodiffusion.SLA.core import", "fail" if args.require_sagesla else "warn", required=args.require_sagesla, detail=f"{type(exc).__name__}: {exc}")
        if args.show_traceback:
            add(checks, "turbodiffusion.SLA.core traceback", "warn", detail=traceback.format_exc())

    # Informational source-layout top-level imports. Missing top-level modules are
    # not fatal for installed-package APIs, but matter for source-authored scripts.
    top_level = {name: module_spec_exists(name) for name in ["ops", "SLA", "rcm", "imaginaire", "serve", "modify_model"]}
    add(
        checks,
        "source-layout top-level import signal",
        "pass" if any(top_level.values()) else "warn",
        required=False,
        detail=(
            "some source-layout top-level modules are importable"
            if any(top_level.values())
            else "top-level source modules are not importable; source scripts may need PYTHONPATH=<inner source directory>"
        ),
        **top_level,
    )

    if torch_mod is not None and ops_mod is not None and bool(getattr(torch_mod.cuda, "is_available")()):
        try:
            count = int(torch_mod.cuda.device_count())
            if count > 0:
                device_index = min(max(args.device, 0), count - 1)
                run_cuda_smokes(checks, torch_mod, ops_mod, device_index)
            else:
                add(checks, "tiny CUDA custom-op/FastNorm smokes", "skip", detail="no CUDA devices reported")
        except Exception as exc:
            add(checks, "tiny CUDA custom-op/FastNorm smokes", "fail", required=True, detail=f"{type(exc).__name__}: {exc}")
            if args.show_traceback:
                add(checks, "tiny CUDA custom-op/FastNorm traceback", "warn", detail=traceback.format_exc())
    else:
        add(checks, "tiny CUDA custom-op/FastNorm smokes", "skip", required=False, detail="requires torch CUDA and turbodiffusion.ops")

    if args.sla_forward_smoke:
        if torch_mod is not None and sla_core is not None and bool(getattr(torch_mod.cuda, "is_available")()):
            run_optional_sla_smoke(checks, torch_mod, sla_core, min(max(args.device, 0), int(torch_mod.cuda.device_count()) - 1))
        else:
            add(checks, "SparseLinearAttention optional tiny random forward", "skip", detail="requires CUDA and turbodiffusion.SLA.core")
    else:
        add(checks, "SparseLinearAttention optional tiny random forward", "skip", detail="not requested; pass --sla-forward-smoke to run warning-only SLA random forward")

    failed_required = [check for check in checks if check.required and check.status == "fail"]
    overall = "fail" if failed_required else "pass"
    summary = {
        "overall": overall,
        "failed_required": [check.name for check in failed_required],
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }

    payload = {"summary": summary, "checks": [asdict(check) for check in checks]}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(checks, summary))

    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())

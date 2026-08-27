#!/usr/bin/env python3
"""Check DPM-Solver backend imports and optional tiny smoke tests.

This script is self-contained inside the generated dpm-solver skill. It imports
the bundled solver copies from the same directory, not from an original source
checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import traceback
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent


def import_from_file(module_name: str, filename: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def torch_check(smoke: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"backend": "torch", "ok": False}
    import torch  # type: ignore

    result.update(
        {
            "torch_version": getattr(torch, "__version__", "unknown"),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    mod = import_from_file("skill_dpm_solver_pytorch", "dpm_solver_pytorch.py")
    result["public_objects"] = [
        name
        for name in ["NoiseScheduleVP", "model_wrapper", "DPM_Solver", "interpolate_fn", "expand_dims"]
        if hasattr(mod, name)
    ]
    if smoke:
        ns = mod.NoiseScheduleVP(schedule="linear")
        solver = mod.DPM_Solver(lambda x, t: torch.zeros_like(x), ns, algorithm_type="dpmsolver")
        x = torch.ones(2, 3)
        out = solver.sample(x, steps=2, order=1, method="multistep")
        result["smoke"] = {"shape": list(out.shape), "finite": bool(torch.isfinite(out).all())}
    result["ok"] = True
    return result


def jax_check(smoke: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"backend": "jax", "ok": False}
    import jax  # type: ignore
    import jax.numpy as jnp  # type: ignore

    result.update(
        {
            "jax_version": getattr(jax, "__version__", "unknown"),
            "devices": [str(device) for device in jax.devices()],
        }
    )
    mod = import_from_file("skill_dpm_solver_jax", "dpm_solver_jax.py")
    result["public_objects"] = [
        name
        for name in ["NoiseScheduleVP", "model_wrapper", "DPM_Solver", "interpolate_fn", "expand_dims", "to_sparse_list"]
        if hasattr(mod, name)
    ]
    if smoke:
        ns = mod.NoiseScheduleVP(schedule="linear")
        solver = mod.DPM_Solver(lambda x, t: jnp.zeros_like(x), ns, predict_x0=False)
        x = jnp.ones((2, 3))
        out = solver.sample(x, steps=2, order=1, method="multistep")
        result["smoke"] = {"shape": list(out.shape), "finite": bool(jnp.isfinite(out).all())}
    result["ok"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["torch", "jax", "both"], default="both")
    parser.add_argument("--smoke", action="store_true", help="run tiny zero-model sampling checks")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON only")
    args = parser.parse_args()

    checks = []
    for backend, fn in [("torch", torch_check), ("jax", jax_check)]:
        if args.backend not in (backend, "both"):
            continue
        try:
            checks.append(fn(args.smoke))
        except Exception as exc:  # pragma: no cover - diagnostic script
            checks.append(
                {
                    "backend": backend,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback_tail": traceback.format_exc().splitlines()[-8:],
                }
            )

    payload = {"ok": all(item.get("ok") for item in checks), "checks": checks}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in checks:
            status = "PASS" if item.get("ok") else "FAIL"
            print(f"[{status}] {item['backend']}")
            for key, value in item.items():
                if key not in {"backend", "ok"}:
                    print(f"  {key}: {value}")
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

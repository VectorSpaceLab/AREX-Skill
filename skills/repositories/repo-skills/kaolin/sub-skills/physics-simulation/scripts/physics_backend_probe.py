#!/usr/bin/env python3
"""Safe Kaolin physics backend probe.

The probe checks imports, torch/CUDA visibility, Warp availability, optional
Newton coupling imports, and optionally runs tiny construction/simulation smokes.
It is designed to run from any working directory and does not depend on the
original repository checkout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from typing import Any, Dict, List, Tuple


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _module_version(module: Any) -> str | None:
    for attr in ("__version__", "version", "VERSION"):
        value = getattr(module, attr, None)
        if value is not None:
            return str(value)
    return None


def _import_module(name: str) -> Tuple[Any | None, Dict[str, Any]]:
    check: Dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
        check.update({"ok": True, "version": _module_version(module)})
        return module, check
    except Exception as exc:  # pragma: no cover - depends on host env
        check.update({
            "errorType": type(exc).__name__,
            "error": str(exc),
        })
        return None, check


def _record(checks: List[Dict[str, Any]], name: str, ok: bool, **extra: Any) -> None:
    row = {"name": name, "ok": bool(ok)}
    row.update({k: _jsonable(v) for k, v in extra.items() if v is not None})
    checks.append(row)


def _create_rigid_compat(simplicits: Any, physics_points: Any, pts: Any) -> Tuple[Any, str]:
    """Create a rigid object with current API, falling back for older installs."""
    try:
        return simplicits.SimplicitsObject.create_rigid(physics_points=physics_points), "physics_points"
    except TypeError:
        # Older Kaolin wheels accepted only pts/yms/prs/rhos/appx_vol. The generated
        # skill documents the current API, but the probe should still report useful
        # backend information when run against an older installed package.
        return simplicits.SimplicitsObject.create_rigid(
            pts=pts,
            yms=physics_points.yms,
            prs=physics_points.prs,
            rhos=physics_points.rhos,
            appx_vol=physics_points.appx_vol,
        ), "legacy_args"


def run_probe(args: argparse.Namespace) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []
    errors: List[str] = []

    result: Dict[str, Any] = {
        "tool": "physics_backend_probe",
        "ok": True,
        "requirements": {
            "require_cuda": args.require_cuda,
            "require_warp": args.require_warp,
            "require_newton": args.require_newton,
            "simulation_smoke": args.simulation_smoke,
        },
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }

    torch, torch_check = _import_module("torch")
    checks.append({"name": "import torch", **torch_check})
    if torch is None:
        errors.append("PyTorch import failed; Kaolin physics cannot be probed.")
        result["ok"] = False
        return result

    cuda_available = bool(torch.cuda.is_available())
    cuda_info: Dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": cuda_available,
        "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
    }
    if cuda_available:
        try:
            cuda_info["current_device"] = torch.cuda.current_device()
            cuda_info["device_name"] = torch.cuda.get_device_name(torch.cuda.current_device())
        except Exception as exc:  # pragma: no cover - host dependent
            cuda_info["device_query_error"] = f"{type(exc).__name__}: {exc}"
    _record(checks, "torch cuda", True, **cuda_info)

    if args.require_cuda and not cuda_available:
        errors.append("CUDA was required but torch.cuda.is_available() is false.")

    kaolin, kaolin_check = _import_module("kaolin")
    checks.append({"name": "import kaolin", **kaolin_check})
    if kaolin is None:
        errors.append("Kaolin import failed.")
        result["ok"] = False
        return result

    warp, warp_check = _import_module("warp")
    checks.append({"name": "import warp", **warp_check})
    if warp is None:
        msg = "Warp import failed; Simplicits scene stepping and materials are not runnable."
        if args.require_warp or args.simulation_smoke:
            errors.append(msg)
        else:
            warnings.append(msg)
    else:
        try:
            warp.init()
            _record(checks, "warp init", True)
        except Exception as exc:  # pragma: no cover - host dependent
            _record(checks, "warp init", False, errorType=type(exc).__name__, error=str(exc))
            if args.require_warp or args.simulation_smoke:
                errors.append("Warp imported but warp.init() failed.")
            else:
                warnings.append("Warp imported but warp.init() failed; simulation may be unavailable.")

    simplicits, simplicits_check = _import_module("kaolin.physics.simplicits")
    checks.append({"name": "import kaolin.physics.simplicits", **simplicits_check})
    materials, materials_check = _import_module("kaolin.physics.materials")
    checks.append({"name": "import kaolin.physics.materials", **materials_check})
    missing_simplicits_api: List[str] = []
    if simplicits is None:
        errors.append("kaolin.physics.simplicits import failed.")
    else:
        required_api = ["PhysicsPoints", "SimplicitsObject", "SkinnedPhysicsPoints", "SimplicitsScene"]
        missing_simplicits_api = [name for name in required_api if not hasattr(simplicits, name)]
        _record(
            checks,
            "simplicits current API surface",
            not missing_simplicits_api,
            missing=missing_simplicits_api,
        )
        if missing_simplicits_api:
            errors.append(
                "Installed kaolin.physics.simplicits is missing current APIs: "
                + ", ".join(missing_simplicits_api)
                + ". Install a Kaolin build matching this skill before running current Simplicits workflows."
            )
    if materials is None:
        warnings.append("kaolin.physics.materials import failed; material-energy APIs unavailable.")

    newton, newton_check = _import_module("newton")
    checks.append({"name": "import newton", **newton_check})
    exp_newton = None
    if newton is not None:
        exp_newton, exp_newton_check = _import_module("kaolin.experimental.newton")
        checks.append({"name": "import kaolin.experimental.newton", **exp_newton_check})
    else:
        warnings.append("Optional Newton package is not importable; experimental coupling is gated off.")
    if args.require_newton and (newton is None or exp_newton is None):
        errors.append("Newton coupling was required but newton / kaolin.experimental.newton did not import.")

    construction_device = args.device
    if construction_device == "auto":
        construction_device = "cuda" if cuda_available else "cpu"
    if construction_device == "cuda" and not cuda_available:
        warnings.append("Requested construction device cuda but CUDA is unavailable; construction smoke skipped.")
    elif not args.skip_construction_smoke and simplicits is not None and not missing_simplicits_api:
        try:
            n = max(4, int(args.num_points))
            pts = torch.rand(n, 3, device=construction_device, dtype=torch.float32) - 0.5
            physics_points = simplicits.PhysicsPoints(
                pts=pts,
                yms=1.0e4,
                prs=0.45,
                rhos=500.0,
                appx_vol=1.0,
            )
            sim_obj, create_api = _create_rigid_compat(simplicits, physics_points, pts)
            weights = sim_obj.skinning_mod.compute_skinning_weights(pts[:2])
            _record(
                checks,
                "tiny PhysicsPoints/create_rigid smoke",
                True,
                device=construction_device,
                points=list(physics_points.pts.shape),
                weights=list(weights.shape),
                num_handles=getattr(sim_obj, "num_handles", None),
                create_api=create_api,
            )
        except Exception as exc:  # pragma: no cover - host dependent
            _record(
                checks,
                "tiny PhysicsPoints/create_rigid smoke",
                False,
                device=construction_device,
                errorType=type(exc).__name__,
                error=str(exc),
                traceback=traceback.format_exc() if args.verbose else None,
            )
            errors.append("Tiny PhysicsPoints/create_rigid smoke failed.")

    if args.simulation_smoke:
        if simplicits is None:
            errors.append("Simulation smoke requested but simplicits import failed.")
        elif missing_simplicits_api:
            errors.append("Simulation smoke requested but current Simplicits APIs are missing.")
        elif not cuda_available and (args.device in ("auto", "cuda")):
            errors.append("Simulation smoke requested but CUDA is unavailable.")
        else:
            sim_device = "cuda" if args.device == "auto" else args.device
            if sim_device != "cuda":
                warnings.append("Simulation smoke is normally CUDA/Warp-gated; non-CUDA device requested.")
            try:
                n = max(8, int(args.num_points))
                q = max(4, min(int(args.num_qp), n))
                pts = torch.rand(n, 3, device=sim_device, dtype=torch.float32) - 0.5
                physics_points = simplicits.PhysicsPoints(
                    pts=pts,
                    yms=1.0e4,
                    prs=0.45,
                    rhos=500.0,
                    appx_vol=1.0,
                )
                sim_obj, create_api = _create_rigid_compat(simplicits, physics_points, pts)
                scene = simplicits.SimplicitsScene(device=sim_device)
                scene.max_newton_steps = 1
                obj_id = scene.add_object(sim_obj, num_qp=q, renderable_pts=pts.clone())
                scene.set_scene_gravity(acc_gravity=torch.tensor([0.0, 9.8, 0.0], device=sim_device))
                for _ in range(max(1, int(args.max_steps))):
                    scene.run_sim_step()
                deformed = scene.get_object_deformed_pts(obj_id, "rendered")
                _record(
                    checks,
                    "tiny SimplicitsScene simulation smoke",
                    True,
                    device=sim_device,
                    num_qp=q,
                    steps=max(1, int(args.max_steps)),
                    deformed_shape=list(deformed.shape),
                    create_api=create_api,
                )
            except Exception as exc:  # pragma: no cover - host dependent
                _record(
                    checks,
                    "tiny SimplicitsScene simulation smoke",
                    False,
                    device=sim_device,
                    errorType=type(exc).__name__,
                    error=str(exc),
                    traceback=traceback.format_exc() if args.verbose else None,
                )
                errors.append("Tiny SimplicitsScene simulation smoke failed.")

    if errors:
        result["ok"] = False
    return result


def print_human(result: Dict[str, Any]) -> None:
    print(f"Kaolin physics backend probe: {'OK' if result['ok'] else 'FAILED'}")
    for check in result["checks"]:
        status = "ok" if check.get("ok") else "FAIL"
        name = check.get("name") or check.get("module")
        detail_parts = []
        for key in ("version", "torch_version", "torch_cuda_version", "cuda_available", "device", "num_handles", "error"):
            if key in check and check[key] is not None:
                detail_parts.append(f"{key}={check[key]}")
        detail = f" ({', '.join(detail_parts)})" if detail_parts else ""
        print(f"- {status}: {name}{detail}")
    if result["warnings"]:
        print("Warnings:")
        for item in result["warnings"]:
            print(f"- {item}")
    if result["errors"]:
        print("Errors:")
        for item in result["errors"]:
            print(f"- {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Kaolin physics/Simplicits backends safely without depending on a source checkout.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--verbose", action="store_true", help="Include tracebacks for failed smokes.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--require-warp", action="store_true", help="Fail if Warp import/init fails.")
    parser.add_argument("--require-newton", action="store_true", help="Fail if optional Newton coupling imports fail.")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device for tiny construction/simulation smokes. Default: auto.",
    )
    parser.add_argument(
        "--skip-construction-smoke",
        action="store_true",
        help="Only check imports/devices; do not construct PhysicsPoints/create_rigid.",
    )
    parser.add_argument(
        "--simulation-smoke",
        action="store_true",
        help="Run one tiny SimplicitsScene step. This may compile Warp kernels; off by default.",
    )
    parser.add_argument("--num-points", type=int, default=32, help="Tiny smoke point count. Default: 32.")
    parser.add_argument("--num-qp", type=int, default=16, help="Tiny scene quadrature count. Default: 16.")
    parser.add_argument("--max-steps", type=int, default=1, help="Tiny scene steps if --simulation-smoke is set. Default: 1.")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_probe(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

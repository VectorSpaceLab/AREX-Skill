#!/usr/bin/env python3
"""Kaolin render backend probe.

By default this only imports modules and reports CUDA/nvdiffrast availability.
Use --probe-rasterize for a tiny CUDA/nvdiffrast rasterization smoke when safe.
"""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any, Dict


def import_ok(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def rasterize_probe(backend: str) -> Dict[str, Any]:
    import torch
    from kaolin.render.mesh.rasterization import rasterize

    if backend.startswith("cuda") and not torch.cuda.is_available():
        return {"ok": False, "reason": "CUDA is not available"}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    face_vertices_z = torch.ones((1, 1, 3), device=device, dtype=torch.float32)
    face_vertices_image = torch.tensor(
        [[[[0.0, 0.0], [0.5, 0.0], [0.0, 0.5]]]], device=device, dtype=torch.float32
    )
    face_features = [torch.ones((1, 1, 3, 1), device=device, dtype=torch.float32)]
    image, face_idx = rasterize(
        4,
        4,
        face_vertices_z,
        face_vertices_image,
        face_features,
        backend=backend,
    )
    return {
        "ok": True,
        "backend": backend,
        "device": device,
        "image_shape": list(image[0].shape if isinstance(image, (list, tuple)) else image.shape),
        "face_idx_shape": list(face_idx.shape),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Kaolin rendering backend availability safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--probe-rasterize", action="store_true", help="Run a tiny rasterization smoke.")
    parser.add_argument("--backend", default="cuda", choices=["cuda", "nvdiffrast", "nvdiffrast_fwd"], help="Backend for --probe-rasterize.")
    args = parser.parse_args()

    import torch

    report: Dict[str, Any] = {
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "imports": {
            name: import_ok(name)
            for name in [
                "kaolin",
                "kaolin._C",
                "kaolin.render.mesh.rasterization",
                "kaolin.render.mesh.dibr",
                "kaolin.render.easy_render",
                "nvdiffrast",
            ]
        },
    }
    if args.probe_rasterize:
        try:
            report["rasterize"] = rasterize_probe(args.backend)
        except Exception as exc:
            report["rasterize"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    ok = report["imports"]["kaolin"]["ok"] and report["imports"]["kaolin.render.easy_render"]["ok"]
    if args.probe_rasterize:
        ok = ok and report.get("rasterize", {}).get("ok", False)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe Kaolin geometry/I/O environment and asset probe.

Examples:
  python mesh_io_probe.py --help
  python mesh_io_probe.py --check-imports --json
  python mesh_io_probe.py --tiny-surface-mesh --json
  python mesh_io_probe.py --kind mesh ./asset.obj --triangulate --json
  python mesh_io_probe.py --kind gaussian ./scene.ply --json
  python mesh_io_probe.py --kind usd-paths ./scene.usdc --json

The script performs read-only imports and optional file reads. It never downloads
data, launches viewers, mutates datasets, or overwrites assets.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Any, Dict, Optional


def import_status(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "module": name, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"ok": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def tensor_summary(value: Any) -> Any:
    if hasattr(value, "shape"):
        return {"shape": list(value.shape), "dtype": str(getattr(value, "dtype", "")), "device": str(getattr(value, "device", ""))}
    if isinstance(value, (list, tuple)):
        return [tensor_summary(v) for v in value[:4]] + (["..."] if len(value) > 4 else [])
    return type(value).__name__


def tiny_surface_mesh() -> Dict[str, Any]:
    import torch
    from kaolin.rep.surface_mesh import SurfaceMesh

    vertices = torch.tensor(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        dtype=torch.float32,
    )
    faces = torch.tensor([[0, 1, 2]], dtype=torch.long)
    mesh = SurfaceMesh(vertices=vertices, faces=faces)
    return {
        "ok": True,
        "container": type(mesh).__name__,
        "vertices": tensor_summary(mesh.vertices),
        "faces": tensor_summary(mesh.faces),
    }


def probe_mesh(path: str, triangulate: bool) -> Dict[str, Any]:
    import kaolin as kal

    mesh = kal.io.import_mesh(path, triangulate=triangulate)
    return {
        "ok": True,
        "type": type(mesh).__name__,
        "vertices": tensor_summary(getattr(mesh, "vertices", None)),
        "faces": tensor_summary(getattr(mesh, "faces", None)),
        "has_materials": bool(getattr(mesh, "materials", None)),
        "has_uvs": getattr(mesh, "uvs", None) is not None,
        "has_normals": getattr(mesh, "normals", None) is not None or getattr(mesh, "face_normals", None) is not None,
    }


def probe_gaussian(path: str) -> Dict[str, Any]:
    import kaolin as kal

    if hasattr(kal.io, "import_gaussiancloud"):
        cloud = kal.io.import_gaussiancloud(path)
    else:
        from kaolin.io import gaussians
        cloud = gaussians.import_gaussiancloud(path)
    fields = {name: tensor_summary(getattr(cloud, name)) for name in ["positions", "orientations", "scales", "opacities", "sh_coeff"] if hasattr(cloud, name)}
    return {"ok": True, "type": type(cloud).__name__, "fields": fields}


def probe_usd_paths(path: str) -> Dict[str, Any]:
    from pxr import Usd

    stage = Usd.Stage.Open(path)
    if stage is None:
        return {"ok": False, "error": "Usd.Stage.Open returned None"}
    prims = [str(prim.GetPath()) for prim in stage.Traverse()][:200]
    return {"ok": True, "prim_count_reported": len(prims), "prim_paths": prims}


def probe_asset(kind: Optional[str], path: Optional[str], triangulate: bool) -> Dict[str, Any]:
    if not kind:
        return {"ok": True, "skipped": "no --kind provided"}
    if not path:
        return {"ok": False, "error": "--kind requires a file path"}
    if not os.path.exists(path):
        return {"ok": False, "error": f"file does not exist: {path}"}
    try:
        if kind == "mesh":
            return probe_mesh(path, triangulate=triangulate)
        if kind == "gaussian":
            return probe_gaussian(path)
        if kind == "usd-paths":
            return probe_usd_paths(path)
        return {"ok": False, "error": f"unsupported kind: {kind}"}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Kaolin geometry/I/O capabilities safely.")
    parser.add_argument("path", nargs="?", help="Optional asset path for --kind mesh|gaussian|usd-paths.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text.")
    parser.add_argument("--check-imports", action="store_true", help="Check imports only unless --kind is also provided.")
    parser.add_argument("--tiny-surface-mesh", action="store_true", help="Construct a tiny in-memory SurfaceMesh.")
    parser.add_argument("--kind", choices=["mesh", "gaussian", "usd-paths"], help="Optionally read and summarize one asset.")
    parser.add_argument("--triangulate", action="store_true", help="Pass triangulate=True for --kind mesh.")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "imports": {
            name: import_status(name)
            for name in [
                "kaolin",
                "kaolin.io",
                "kaolin.io.usd",
                "kaolin.rep.surface_mesh",
                "kaolin.rep.spc",
                "kaolin.rep.gaussians",
                "pxr",
                "plyfile",
                "pygltflib",
                "PIL",
            ]
        },
    }
    if args.tiny_surface_mesh:
        try:
            report["tiny_surface_mesh"] = tiny_surface_mesh()
        except Exception as exc:  # pragma: no cover
            report["tiny_surface_mesh"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.kind:
        report["asset"] = probe_asset(args.kind, args.path, args.triangulate)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, info in report["imports"].items():
            marker = "OK" if info["ok"] else "MISSING"
            print(f"{marker:7s} {name} {info.get('version') or info.get('error') or ''}")
        if "tiny_surface_mesh" in report:
            print("tiny_surface_mesh:", report["tiny_surface_mesh"])
        if "asset" in report:
            print("asset:", report["asset"])
    ok = report["imports"]["kaolin"]["ok"]
    if "asset" in report:
        ok = ok and report["asset"].get("ok", False)
    if "tiny_surface_mesh" in report:
        ok = ok and report["tiny_surface_mesh"].get("ok", False)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

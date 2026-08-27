#!/usr/bin/env python3
"""Check Hunyuan3D-2 installation and backend readiness without downloading model weights."""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version


def check_import(name: str) -> dict:
    try:
        importlib.import_module(name)
        return {"name": name, "status": "ok"}
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"name": name, "status": "fail", "error": repr(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Hunyuan3D-2 package/backend readiness.")
    parser.add_argument("--check-cuda", action="store_true", help="Check torch CUDA availability and allocate a tiny tensor.")
    parser.add_argument("--check-extensions", action="store_true", help="Import mesh_processor/custom_rasterizer and construct MeshRender if CUDA is requested.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of readable text.")
    args = parser.parse_args()

    result = {"python": sys.version.split()[0], "distributions": {}, "imports": [], "cuda": None, "extensions": None}
    for dist in ["hy3dgen", "torch", "torchvision", "custom_rasterizer", "mesh_processor"]:
        try:
            result["distributions"][dist] = version(dist)
        except PackageNotFoundError:
            result["distributions"][dist] = None

    for module in ["hy3dgen", "hy3dgen.shapegen", "hy3dgen.texgen", "hy3dgen.rembg", "hy3dgen.text2image"]:
        result["imports"].append(check_import(module))

    torch_mod = None
    if args.check_cuda or args.check_extensions:
        try:
            import torch
            torch_mod = torch
            cuda = {"torch_version": torch.__version__, "available": bool(torch.cuda.is_available()), "device_count": 0, "allocation": "not-run"}
            if torch.cuda.is_available():
                cuda["device_count"] = torch.cuda.device_count()
                cuda["device_name_0"] = torch.cuda.get_device_name(0)
                torch.empty((1,), device="cuda")
                cuda["allocation"] = "ok"
            result["cuda"] = cuda
        except Exception as exc:  # noqa: BLE001
            result["cuda"] = {"available": False, "error": repr(exc)}

    if args.check_extensions:
        ext = {"imports": [], "mesh_render_cuda": "not-run"}
        for module in ["mesh_processor", "custom_rasterizer"]:
            ext["imports"].append(check_import(module))
        if torch_mod is not None and result.get("cuda", {}).get("available"):
            try:
                from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
                MeshRender(device="cuda")
                ext["mesh_render_cuda"] = "ok"
            except Exception as exc:  # noqa: BLE001
                ext["mesh_render_cuda"] = f"fail: {exc!r}"
        result["extensions"] = ext

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print("Distributions:")
        for key, value in result["distributions"].items():
            print(f"  {key}: {value}")
        print("Imports:")
        for item in result["imports"]:
            line = f"  {item['name']}: {item['status']}"
            if item["status"] != "ok":
                line += f" ({item['error']})"
            print(line)
        if result["cuda"] is not None:
            print(f"CUDA: {result['cuda']}")
        if result["extensions"] is not None:
            print(f"Extensions: {result['extensions']}")

    failed = any(item["status"] != "ok" for item in result["imports"])
    if args.check_extensions:
        failed = failed or any(item["status"] != "ok" for item in result["extensions"]["imports"])
        if args.check_cuda:
            failed = failed or result["extensions"].get("mesh_render_cuda") != "ok"
    if args.check_cuda:
        failed = failed or not result.get("cuda", {}).get("available")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()

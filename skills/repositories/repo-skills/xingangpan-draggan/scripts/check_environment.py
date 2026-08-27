#!/usr/bin/env python3
"""Check a DragGAN/StyleGAN runtime environment without launching GUIs or downloads.

This helper is bundled with the DisCo DragGAN skill. It can be run from any
working directory and optionally points at a local DragGAN checkout to validate
repo imports.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path


def try_import(name: str):
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic surface
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DragGAN runtime imports and optional CUDA availability.")
    parser.add_argument("--repo-root", type=Path, help="Optional local DragGAN checkout to add to sys.path for import checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if args.repo_root:
        repo_root = args.repo_root.expanduser().resolve()
        if not repo_root.exists():
            print(f"ERROR: --repo-root does not exist: {repo_root}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(repo_root))

    modules = [
        "torch",
        "torchvision",
        "numpy",
        "scipy",
        "PIL",
        "click",
        "gradio",
        "OpenGL",
        "glfw",
        "imgui",
        "imageio",
        "cv2",
        "pandas",
        "moviepy.editor",
        "lpips",
        "dnnlib",
        "legacy",
        "torch_utils",
        "training",
        "viz.renderer",
        "gradio_utils",
        "gui_utils",
    ]
    results = [try_import(m) for m in modules]

    cuda = {"checked": False, "available": False}
    torch_result = next((r for r in results if r["name"] == "torch" and r["ok"]), None)
    if torch_result:
        import torch  # type: ignore

        cuda = {
            "checked": True,
            "torch": getattr(torch, "__version__", None),
            "torch_cuda": getattr(torch.version, "cuda", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "devices": [],
        }
        if torch.cuda.is_available():
            for idx in range(torch.cuda.device_count()):
                cuda["devices"].append(
                    {
                        "index": idx,
                        "name": torch.cuda.get_device_name(idx),
                        "capability": list(torch.cuda.get_device_capability(idx)),
                    }
                )
            try:
                torch.empty((1,), device="cuda")
                cuda["tiny_allocation"] = True
            except Exception as exc:  # noqa: BLE001
                cuda["tiny_allocation"] = False
                cuda["allocation_error"] = f"{type(exc).__name__}: {exc}"

    payload = {"imports": results, "cuda": cuda}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for r in results:
            if r["ok"]:
                suffix = f" ({r['version']})" if r.get("version") else ""
                print(f"OK import {r['name']}{suffix}")
            else:
                print(f"FAIL import {r['name']}: {r['error']}")
        if cuda["checked"]:
            print(f"CUDA available: {cuda['available']} device_count={cuda.get('device_count', 0)} torch_cuda={cuda.get('torch_cuda')}")
            for d in cuda.get("devices", []):
                print(f"  cuda:{d['index']} {d['name']} capability={tuple(d['capability'])}")

    required = {"torch", "dnnlib", "legacy", "training", "viz.renderer"}
    failed_required = [r for r in results if r["name"] in required and not r["ok"]]
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""MAGI-1 runtime preflight without model loading.

Checks Python/runtime dependencies, CUDA visibility, ffmpeg availability, and
optional source asset paths. It never imports MAGI pipeline modules, starts
`torch.distributed`, loads T5/VAE/DiT weights, or runs generation.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEPENDENCIES = [
    ("torch", "PyTorch"),
    ("flash_attn", "flash-attn"),
    ("flashinfer", "flashinfer-python"),
    ("diffusers", "diffusers"),
    ("transformers", "transformers"),
    ("einops", "einops"),
    ("ffmpeg", "ffmpeg-python"),
    ("imageio", "imageio"),
    ("PIL", "Pillow"),
    ("numpy", "numpy"),
    ("safetensors", "safetensors"),
    ("timm", "timm"),
    ("torchdiffeq", "torchdiffeq"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a MAGI-1 runtime environment without loading model weights or running generation."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Optional MAGI source/plugin root used to check example assets and source subtrees.",
    )
    parser.add_argument(
        "--run-cuda-smoke",
        action="store_true",
        help="If CUDA is available, allocate a tiny tensor on CUDA and move the result back to CPU.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def dependency_report() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for module_name, package_name in DEPENDENCIES:
        row: dict[str, Any] = {"module": module_name, "package": package_name, "ok": False}
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - preflight should report import failures, not crash.
            row["error"] = f"{type(exc).__name__}: {exc}"
        else:
            row["ok"] = True
            row["version"] = getattr(module, "__version__", "unknown")
        rows.append(row)
    return rows


def ffmpeg_report() -> dict[str, Any]:
    exe = shutil.which("ffmpeg")
    row: dict[str, Any] = {"executable": exe, "ok": bool(exe)}
    if exe:
        try:
            proc = subprocess.run([exe, "-version"], text=True, capture_output=True, timeout=10, check=False)
        except Exception as exc:  # noqa: BLE001
            row["ok"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"
        else:
            first_line = (proc.stdout or proc.stderr).splitlines()[:1]
            row["returncode"] = proc.returncode
            row["version_line"] = first_line[0] if first_line else ""
            row["ok"] = proc.returncode == 0
    return row


def torch_report(run_cuda_smoke: bool) -> dict[str, Any]:
    row: dict[str, Any] = {"import_ok": False, "cuda_smoke": "not-requested"}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row

    row.update(
        {
            "import_ok": True,
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
        }
    )
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        try:
            row["cuda_device_0"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # noqa: BLE001
            row["cuda_device_0_error"] = f"{type(exc).__name__}: {exc}"
    if run_cuda_smoke:
        if not row["cuda_available"]:
            row["cuda_smoke"] = "skipped-no-cuda"
        else:
            try:
                tensor = torch.tensor([1.0], device="cuda")
                value = float((tensor + 1).cpu().item())
            except Exception as exc:  # noqa: BLE001
                row["cuda_smoke"] = "failed"
                row["cuda_smoke_error"] = f"{type(exc).__name__}: {exc}"
            else:
                row["cuda_smoke"] = "passed"
                row["cuda_smoke_value"] = value
    return row


def source_root_report(source_root: Path | None) -> dict[str, Any]:
    if source_root is None:
        return {"checked": False}
    root = source_root.expanduser().resolve()
    required = [
        "README.md",
        "requirements.txt",
        "inference/pipeline/entry.py",
        "inference/common/config.py",
        "example/assets/special_tokens.npz",
        "comfyui/comfy_nodes.py",
    ]
    files = []
    for rel in required:
        path = root / rel
        files.append({"path": rel, "exists": path.exists()})
    return {"checked": True, "root": str(root), "files": files, "ok": all(item["exists"] for item in files)}


def overall_ok(report: dict[str, Any]) -> bool:
    deps_ok = all(row["ok"] for row in report["dependencies"])
    torch_ok = report["torch"].get("import_ok") and report["torch"].get("cuda_available")
    cuda_smoke = report["torch"].get("cuda_smoke")
    cuda_smoke_ok = cuda_smoke in {"not-requested", "passed"}
    ffmpeg_ok = report["ffmpeg"].get("ok")
    source = report["source_root"]
    source_ok = (not source.get("checked")) or source.get("ok")
    return bool(deps_ok and torch_ok and cuda_smoke_ok and ffmpeg_ok and source_ok)


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "python": {"version": sys.version, "executable": sys.executable},
        "dependencies": dependency_report(),
        "torch": torch_report(args.run_cuda_smoke),
        "ffmpeg": ffmpeg_report(),
        "source_root": source_root_report(args.source_root),
    }
    report["ok"] = overall_ok(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MAGI-1 runtime preflight (no model loading)")
        print(f"Python: {report['python']['version'].splitlines()[0]}")
        print("Dependencies:")
        for dep in report["dependencies"]:
            status = "OK" if dep["ok"] else "FAIL"
            detail = dep.get("version") or dep.get("error") or ""
            print(f"  - {status}: {dep['package']} ({dep['module']}) {detail}")
        torch = report["torch"]
        print("Torch/CUDA:")
        for key in ("version", "cuda_version", "cuda_available", "cuda_device_count", "cuda_device_0", "cuda_smoke"):
            if key in torch:
                print(f"  - {key}: {torch[key]}")
        if "cuda_smoke_error" in torch:
            print(f"  - cuda_smoke_error: {torch['cuda_smoke_error']}")
        ffmpeg = report["ffmpeg"]
        print("ffmpeg:")
        print(f"  - executable: {ffmpeg.get('executable')}")
        print(f"  - ok: {ffmpeg.get('ok')}")
        if ffmpeg.get("version_line"):
            print(f"  - version: {ffmpeg['version_line']}")
        source = report["source_root"]
        if source.get("checked"):
            print("Source root files:")
            for item in source["files"]:
                status = "OK" if item["exists"] else "MISSING"
                print(f"  - {status}: {item['path']}")
        print(f"Overall: {'OK' if report['ok'] else 'NOT READY'}")
        print("Note: this preflight does not load MAGI checkpoints or generate video.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

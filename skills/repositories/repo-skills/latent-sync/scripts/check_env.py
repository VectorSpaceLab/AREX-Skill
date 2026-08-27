#!/usr/bin/env python3
"""Safe LatentSync environment checker.

This helper verifies repository markers, optional imports, CUDA, ffmpeg,
scenedetect binary/import availability, and bundled demo assets without mutating the tree.

Example:
    python scripts/check_env.py --repo-root /path/to/LatentSync \
      --check-imports --check-cuda --check-ffmpeg --check-scenedetect
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_VERSIONS = {
    "torch": "2.5.1+cu121",
    "torchvision": "0.20.1+cu121",
    "diffusers": "0.32.2",
    "transformers": "4.48.0",
    "decord": "0.6.0",
    "mediapipe": "0.10.11",
    "insightface": "0.7.3",
    "onnxruntime": "1.21.0",
    "gradio": "5.24.0",
    "numpy": "1.26.4",
    "setuptools": "80.9.0",
}

REQUIRED_REPO_MARKERS = [
    Path("README.md"),
    Path("latentsync"),
    Path("preprocess"),
    Path("eval"),
    Path("scripts"),
    Path("configs"),
]

DEMO_ASSETS = [
    Path("assets/demo1_video.mp4"),
    Path("assets/demo1_audio.wav"),
    Path("assets/demo2_video.mp4"),
    Path("assets/demo2_audio.wav"),
    Path("assets/demo3_video.mp4"),
    Path("assets/demo3_audio.wav"),
    Path("latentsync/utils/mask.png"),
]

CORE_IMPORTS = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "decord",
    "mediapipe",
    "insightface",
    "onnxruntime",
    "cv2",
    "kornia",
    "python_speech_features",
    "einops",
]

REPO_IMPORTS = [
    "latentsync",
    "latentsync.pipelines.lipsync_pipeline",
    "latentsync.models.unet",
    "latentsync.models.stable_syncnet",
    "latentsync.whisper.audio2feature",
    "latentsync.data.syncnet_dataset",
    "preprocess.data_processing_pipeline",
    "preprocess.affine_transform",
    "preprocess.sync_av",
    "scripts.inference",
    "scripts.train_unet",
    "scripts.train_syncnet",
    "eval.eval_sync_conf",
    "eval.eval_syncnet_acc",
    "eval.eval_fvd",
    "tools.write_fileslist",
]


class CheckError(RuntimeError):
    """Raised for a user-facing environment problem."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the LatentSync runtime tree, optional imports, CUDA, ffmpeg, scenedetect, and demo assets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=os.environ.get("LATENTSYNC_REPO_ROOT", "."),
        help="LatentSync runtime tree containing README.md, latentsync/, scripts/, preprocess/, eval/, and configs/.",
    )
    parser.add_argument("--check-imports", action="store_true", help="Import the common runtime modules and report versions.")
    parser.add_argument("--check-cuda", action="store_true", help="Verify torch can see and allocate on CUDA.")
    parser.add_argument("--check-ffmpeg", action="store_true", help="Verify ffmpeg is on PATH and reports a version.")
    parser.add_argument("--check-scenedetect", action="store_true", help="Verify the scenedetect CLI and import are available.")
    parser.add_argument("--check-assets", action="store_true", help="Verify the bundled demo media and mask assets exist.")
    parser.add_argument("--strict-versions", action="store_true", help="Fail when imported package versions differ from the verified baseline.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of plain text.")
    return parser.parse_args()


def resolve_repo_root(raw: str | os.PathLike[str]) -> Path:
    root = Path(raw).expanduser().resolve()
    if not root.exists():
        raise CheckError(f"repo root does not exist: {root}")
    return root


def require_repo_markers(root: Path) -> list[str]:
    missing: list[str] = []
    for marker in REQUIRED_REPO_MARKERS:
        path = root / marker
        if not path.exists():
            missing.append(str(marker))
    return missing


def import_version(module_name: str) -> str | None:
    try:
        from importlib import metadata as importlib_metadata
    except Exception:
        return None

    try:
        return importlib_metadata.version(module_name)
    except Exception:
        return None


def check_imports(root: Path, strict_versions: bool) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    for module_name in CORE_IMPORTS + REPO_IMPORTS:
        entry: dict[str, Any] = {"module": module_name}
        try:
            module = importlib.import_module(module_name)
            entry["imported"] = True
            entry["version"] = getattr(module, "__version__", None) or import_version(module_name)
            expected = EXPECTED_VERSIONS.get(module_name)
            if expected is not None:
                entry["expected_version"] = expected
                entry["version_match"] = entry.get("version") == expected
                if strict_versions and not entry["version_match"]:
                    failures.append(f"{module_name}: expected {expected}, got {entry.get('version')}")
            if module_name == "onnxruntime":
                providers = getattr(module, "get_available_providers", lambda: [])()
                entry["available_providers"] = list(providers)
                entry["cuda_execution_provider"] = "CUDAExecutionProvider" in providers
        except Exception as exc:  # noqa: BLE001 - surface the import failure directly.
            entry["imported"] = False
            entry["error"] = str(exc)
            failures.append(f"{module_name}: {exc}")
        results.append(entry)

    return {"checked": True, "modules": results, "failures": failures, "ok": not failures}


def check_cuda() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"checked": True, "imported": False, "error": str(exc), "ok": False}

    result: dict[str, Any] = {
        "checked": True,
        "imported": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
        "allocated": False,
    }

    if result["cuda_available"] and result["device_count"] > 0:
        try:
            _ = torch.tensor([1.0], device="cuda:0")
            result["allocated"] = True
            result["ok"] = True
        except Exception as exc:  # noqa: BLE001
            result["allocation_error"] = str(exc)
            result["ok"] = False
    else:
        result["ok"] = False

    return result


def run_binary_probe(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=20)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}

    combined = completed.stdout or completed.stderr or ""
    first_line = combined.splitlines()[0] if combined.splitlines() else ""
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "first_line": first_line,
    }


def check_binary(name: str, probe_command: list[str]) -> dict[str, Any]:
    path = shutil.which(name)
    result: dict[str, Any] = {"name": name, "found": path is not None, "path": path}
    if path is None:
        result["ok"] = False
        return result
    result.update(run_binary_probe(probe_command))
    return result


def check_assets(root: Path) -> dict[str, Any]:
    entries = []
    missing: list[str] = []
    for rel in DEMO_ASSETS:
        path = root / rel
        present = path.exists() and path.is_file() and os.access(path, os.R_OK)
        entries.append({"path": str(rel), "present": present})
        if not present:
            missing.append(str(rel))
    return {"checked": True, "assets": entries, "missing": missing, "ok": not missing}


def print_human(summary: dict[str, Any]) -> None:
    print(f"repo root: {summary['repo_root']}")
    repo = summary["repo_markers"]
    if repo["ok"]:
        print("repo markers: OK")
    else:
        print("repo markers: FAIL")
        for item in repo.get("missing", []):
            print(f"  missing: {item}")

    for key in ("imports", "cuda", "ffmpeg", "scenedetect", "assets"):
        block = summary.get(key)
        if not block:
            continue
        if block.get("ok"):
            print(f"{key}: OK")
        else:
            print(f"{key}: FAIL")
            if key == "imports":
                for failure in block.get("failures", []):
                    print(f"  {failure}")
            elif key == "cuda" and block.get("error"):
                print(f"  {block['error']}")
            elif key in {"ffmpeg", "scenedetect"} and not block.get("found", True):
                print(f"  {key} not found on PATH")
            elif key == "assets":
                for item in block.get("missing", []):
                    print(f"  missing: {item}")


def main() -> int:
    args = parse_args()
    root = resolve_repo_root(args.repo_root)

    summary: dict[str, Any] = {"schema": "disco.latentsync.check-env.v1", "repo_root": str(root)}
    summary["repo_markers"] = {
        "checked": True,
        "missing": require_repo_markers(root),
    }
    summary["repo_markers"]["ok"] = not summary["repo_markers"]["missing"]

    if args.check_imports:
        summary["imports"] = check_imports(root, strict_versions=args.strict_versions)
    if args.check_cuda:
        summary["cuda"] = check_cuda()
    if args.check_ffmpeg:
        summary["ffmpeg"] = check_binary("ffmpeg", ["ffmpeg", "-version"])
    if args.check_scenedetect:
        summary["scenedetect"] = check_binary("scenedetect", ["scenedetect", "--help"])
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        try:
            module = importlib.import_module("scenedetect")
            summary["scenedetect_import"] = {
                "checked": True,
                "imported": True,
                "version": getattr(module, "__version__", None) or import_version("scenedetect"),
                "ok": True,
            }
        except Exception as exc:  # noqa: BLE001 - surface the import failure directly.
            summary["scenedetect_import"] = {"checked": True, "imported": False, "error": str(exc), "ok": False}
    if args.check_assets:
        summary["assets"] = check_assets(root)

    failures: list[str] = []
    if not summary["repo_markers"]["ok"]:
        failures.extend(f"missing repo marker: {item}" for item in summary["repo_markers"]["missing"])

    imports_block = summary.get("imports")
    if imports_block and not imports_block.get("ok"):
        failures.extend(imports_block.get("failures", []))

    cuda_block = summary.get("cuda")
    if cuda_block and not cuda_block.get("ok"):
        if cuda_block.get("error"):
            failures.append(cuda_block["error"])
        elif not cuda_block.get("cuda_available", False):
            failures.append("CUDA is not available")
        elif not cuda_block.get("allocated", False):
            failures.append(cuda_block.get("allocation_error", "CUDA allocation failed"))

    for key in ("ffmpeg", "scenedetect"):
        block = summary.get(key)
        if block and not block.get("ok"):
            if not block.get("found", True):
                failures.append(f"{key} not found on PATH")
            elif block.get("first_line"):
                failures.append(f"{key} probe failed: {block['first_line']}")
            else:
                failures.append(f"{key} probe failed")

    scenedetect_import = summary.get("scenedetect_import")
    if scenedetect_import and not scenedetect_import.get("ok"):
        failures.append(scenedetect_import.get("error", "scenedetect import failed"))

    assets_block = summary.get("assets")
    if assets_block and not assets_block.get("ok"):
        failures.extend(f"missing asset: {item}" for item in assets_block.get("missing", []))

    summary["failures"] = failures
    summary["ok"] = not failures

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(summary)
        if summary["ok"]:
            print("LatentSync environment: OK")
        else:
            print("LatentSync environment: BLOCKED", file=sys.stderr)
            for failure in failures:
                print(f"ERROR: {failure}", file=sys.stderr)

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

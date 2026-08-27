#!/usr/bin/env python3
"""Safe preflight checks for LatentSync data preparation.

The default check is intentionally lightweight: it validates the local input tree,
source anchors, CLI tools, checkpoint prerequisites, and scratch path without
running the pipeline or mutating videos. Add --check-imports for Python package
smokes and --require-gpu for CUDA-backed stages.
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
    "numpy": "1.26.4",
    "setuptools": "80.9.0",
    "decord": "0.6.0",
    "mediapipe": "0.10.11",
    "onnxruntime": "1.21.0",
}

REQUIRED_SOURCES = [
    Path("README.md"),
    Path("data_processing_pipeline.sh"),
    Path("preprocess/data_processing_pipeline.py"),
    Path("preprocess/remove_broken_videos.py"),
    Path("preprocess/resample_fps_hz.py"),
    Path("preprocess/detect_shot.py"),
    Path("preprocess/segment_videos.py"),
    Path("preprocess/affine_transform.py"),
    Path("preprocess/remove_incorrect_affined.py"),
    Path("preprocess/sync_av.py"),
    Path("preprocess/filter_high_resolution.py"),
    Path("preprocess/filter_visual_quality.py"),
    Path("latentsync/utils/av_reader.py"),
    Path("latentsync/utils/image_processor.py"),
    Path("latentsync/utils/face_detector.py"),
    Path("latentsync/utils/util.py"),
    Path("eval/syncnet_detect.py"),
    Path("eval/hyper_iqa.py"),
    Path("eval/syncnet/syncnet_eval.py"),
    Path("configs/syncnet/syncnet_16_latent.yaml"),
    Path("configs/syncnet/syncnet_16_pixel.yaml"),
    Path("configs/syncnet/syncnet_16_pixel_attn.yaml"),
    Path("configs/syncnet/syncnet_25_pixel.yaml"),
    Path("docs/syncnet_arch.md"),
]

REQUIRED_CHECKPOINTS = [
    Path("checkpoints/auxiliary/syncnet_v2.model"),
    Path("checkpoints/auxiliary/sfd_face.pth"),
    Path("checkpoints/auxiliary/koniq_pretrained.pkl"),
]

CORE_IMPORTS = [
    "torch",
    "torchvision",
    "numpy",
    "setuptools",
    "decord",
    "mediapipe",
    "onnxruntime",
    "cv2",
    "kornia",
    "insightface",
    "scenedetect",
    "python_speech_features",
    "einops",
]

REPO_IMPORTS = [
    "latentsync.utils.av_reader",
    "latentsync.utils.image_processor",
    "latentsync.utils.face_detector",
    "eval.syncnet_detect",
    "eval.hyper_iqa",
    "eval.syncnet.syncnet_eval",
]

RESNET50_CACHE_NAMES = ["resnet50-19c8e357.pth"]


def resolve_relative(path_str: str, base: Path) -> Path:
    path = Path(path_str).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def import_version(module_name: str) -> str | None:
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None
    version = getattr(module, "__version__", None)
    if version is not None:
        return str(version)
    try:
        from importlib import metadata as importlib_metadata

        return importlib_metadata.version(module_name)
    except Exception:
        return None


def run_binary_probe(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=20)
    except Exception as exc:  # pragma: no cover - platform dependent
        return {"ok": False, "error": str(exc)}
    combined = result.stdout or result.stderr or ""
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "first_line": combined.splitlines()[0] if combined.splitlines() else "",
    }


def check_binary(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    result: dict[str, Any] = {"name": name, "found": path is not None, "path": path}
    if path is None:
        return result
    if name == "ffmpeg":
        result.update(run_binary_probe([name, "-version"]))
    elif name == "scenedetect":
        result.update(run_binary_probe([name, "--help"]))
    return result


def inspect_sources(repo_root: Path) -> list[dict[str, Any]]:
    return [{"path": str(rel), "present": (repo_root / rel).exists()} for rel in REQUIRED_SOURCES]


def inspect_checkpoints(repo_root: Path, cpu_only: bool) -> dict[str, Any]:
    entries = [{"path": str(rel), "present": (repo_root / rel).exists()} for rel in REQUIRED_CHECKPOINTS]
    return {"required": not cpu_only, "files": entries}


def inspect_input_tree(input_dir: Path) -> dict[str, Any]:
    mp4_files = sorted(input_dir.rglob("*.mp4")) if input_dir.exists() and input_dir.is_dir() else []
    total_files = 0
    total_dirs = 0
    if input_dir.exists() and input_dir.is_dir():
        for item in input_dir.rglob("*"):
            if item.is_file():
                total_files += 1
            elif item.is_dir():
                total_dirs += 1
    return {
        "exists": input_dir.exists(),
        "is_dir": input_dir.is_dir(),
        "mp4_count": len(mp4_files),
        "total_file_count": total_files,
        "total_dir_count": total_dirs,
        "sample_mp4s": [str(path) for path in mp4_files[:5]],
    }


def inspect_temp_dir(temp_dir: Path) -> dict[str, Any]:
    parent = temp_dir if temp_dir.exists() and temp_dir.is_dir() else temp_dir.parent
    return {
        "path": str(temp_dir),
        "exists": temp_dir.exists(),
        "is_dir_when_present": (not temp_dir.exists()) or temp_dir.is_dir(),
        "parent": str(parent),
        "parent_exists": parent.exists(),
        "parent_writable": os.access(parent, os.W_OK) if parent.exists() else False,
    }


def inspect_python_imports(repo_root: Path, check_imports: bool, strict_versions: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "checked": check_imports,
        "strict_versions": strict_versions,
        "core_modules": [],
        "repo_modules": [],
    }
    if not check_imports:
        return report

    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    for module_name in CORE_IMPORTS:
        entry: dict[str, Any] = {"module": module_name}
        try:
            module = importlib.import_module(module_name)
            entry["imported"] = True
            entry["version"] = getattr(module, "__version__", None) or import_version(module_name)
            expected = EXPECTED_VERSIONS.get(module_name)
            if expected is not None:
                entry["expected_version"] = expected
                entry["version_match"] = entry.get("version") == expected
                if not entry["version_match"]:
                    entry["message"] = f"expected {expected}, got {entry.get('version')}"
            if module_name == "onnxruntime":
                providers = getattr(module, "get_available_providers", lambda: [])()
                entry["available_providers"] = list(providers)
                entry["cuda_execution_provider"] = "CUDAExecutionProvider" in providers
        except Exception as exc:
            entry["imported"] = False
            entry["error"] = str(exc)
        report["core_modules"].append(entry)

    for module_name in REPO_IMPORTS:
        entry = {"module": module_name}
        try:
            importlib.import_module(module_name)
            entry["imported"] = True
        except Exception as exc:
            entry["imported"] = False
            entry["error"] = str(exc)
        report["repo_modules"].append(entry)

    return report


def inspect_gpu(check_imports: bool, require_gpu: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"checked": check_imports or require_gpu}
    if not (check_imports or require_gpu):
        return result

    try:
        import torch  # type: ignore
    except Exception as exc:
        result["imported"] = False
        result["error"] = str(exc)
        return result

    result["imported"] = True
    result["torch_version"] = getattr(torch, "__version__", None)
    result["cuda_available"] = bool(torch.cuda.is_available())
    result["device_count"] = int(torch.cuda.device_count())
    result["can_allocate"] = False
    if result["cuda_available"] and result["device_count"] > 0:
        try:
            _ = torch.tensor([1.0], device="cuda:0")
            result["can_allocate"] = True
        except Exception as exc:
            result["allocation_error"] = str(exc)
    return result


def likely_torch_cache_dirs(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    torch_home = os.environ.get("TORCH_HOME")
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    home = Path.home()
    if torch_home:
        candidates.append(Path(torch_home).expanduser() / "hub" / "checkpoints")
        candidates.append(Path(torch_home).expanduser() / "checkpoints")
    if xdg_cache_home:
        candidates.append(Path(xdg_cache_home).expanduser() / "torch" / "hub" / "checkpoints")
    candidates.append(home / ".cache" / "torch" / "hub" / "checkpoints")
    candidates.append(repo_root / "checkpoints")
    # Preserve order while removing duplicates.
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def inspect_hyperiqa_cache(repo_root: Path, cpu_only: bool) -> dict[str, Any]:
    if cpu_only:
        return {"checked": False, "reason": "cpu_only"}
    dirs = likely_torch_cache_dirs(repo_root)
    hits: list[str] = []
    for cache_dir in dirs:
        for name in RESNET50_CACHE_NAMES:
            path = cache_dir / name
            if path.exists():
                hits.append(str(path))
    return {
        "checked": True,
        "required_for_offline_visual_quality": True,
        "cache_dirs_considered": [str(path) for path in dirs],
        "resnet50_cache_hits": hits,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = resolve_relative(args.repo_root, Path.cwd())
    input_dir = resolve_relative(args.input_dir, repo_root)
    temp_dir = resolve_relative(args.temp_dir, repo_root)
    import_checks = args.check_imports or args.strict_versions

    report: dict[str, Any] = {
        "repo_root": str(repo_root),
        "input_dir": str(input_dir),
        "temp_dir": inspect_temp_dir(temp_dir),
        "input_tree": inspect_input_tree(input_dir),
        "binaries": [check_binary("ffmpeg"), check_binary("scenedetect")],
        "sources": inspect_sources(repo_root),
        "checkpoints": inspect_checkpoints(repo_root, args.cpu_only),
        "imports": inspect_python_imports(repo_root, import_checks, args.strict_versions),
        "gpu": inspect_gpu(import_checks, args.require_gpu),
        "hyperiqa_resnet_cache": inspect_hyperiqa_cache(repo_root, args.cpu_only),
        "warnings": [],
        "errors": [],
        "status": "ready",
    }

    if not Path(report["repo_root"]).exists():
        report["errors"].append(f"Repo root does not exist: {report['repo_root']}")
    elif not Path(report["repo_root"]).is_dir():
        report["errors"].append(f"Repo root is not a directory: {report['repo_root']}")

    tree = report["input_tree"]
    if not tree["exists"]:
        report["errors"].append(f"Input directory does not exist: {input_dir}")
    elif not tree["is_dir"]:
        report["errors"].append(f"Input path is not a directory: {input_dir}")
    elif tree["mp4_count"] == 0:
        report["warnings"].append(f"No .mp4 files were found under {input_dir}")

    temp = report["temp_dir"]
    if not temp["is_dir_when_present"]:
        report["errors"].append(f"Temp path exists but is not a directory: {temp['path']}")
    if not temp["parent_exists"]:
        report["errors"].append(f"Temp directory parent does not exist: {temp['parent']}")
    elif not temp["parent_writable"]:
        report["errors"].append(f"Temp directory parent is not writable: {temp['parent']}")

    for binary in report["binaries"]:
        if not binary["found"]:
            report["errors"].append(f"Missing binary on PATH: {binary['name']}")
        elif binary.get("ok") is False:
            report["warnings"].append(f"Binary probe failed for {binary['name']}: {binary.get('error') or binary.get('first_line')}")

    for src in report["sources"]:
        if not src["present"]:
            report["errors"].append(f"Missing source anchor: {src['path']}")

    if report["checkpoints"]["required"]:
        for ckpt in report["checkpoints"]["files"]:
            if not ckpt["present"]:
                report["errors"].append(f"Missing checkpoint prerequisite: {ckpt['path']}")

    if report["imports"]["checked"]:
        for module in report["imports"]["core_modules"]:
            if not module.get("imported"):
                report["errors"].append(f"Missing Python import: {module['module']} ({module.get('error')})")
            elif args.strict_versions and module.get("expected_version") is not None and not module.get("version_match", True):
                report["errors"].append(f"Version mismatch for {module['module']}: {module.get('message')}")
            elif module.get("expected_version") is not None and not module.get("version_match", True):
                report["warnings"].append(f"Version mismatch for {module['module']}: {module.get('message')}")
            if module["module"] == "onnxruntime" and module.get("imported") and not module.get("cuda_execution_provider", False):
                message = "onnxruntime imported but CUDAExecutionProvider is not available."
                if args.require_gpu:
                    report["errors"].append(message)
                else:
                    report["warnings"].append(message)

        for module in report["imports"]["repo_modules"]:
            if not module.get("imported"):
                report["errors"].append(f"Missing repo import: {module['module']} ({module.get('error')})")

    if report["gpu"].get("checked") and not report["gpu"].get("imported", False):
        report["errors"].append(f"torch import failed: {report['gpu'].get('error', 'unknown error')}")
    elif report["gpu"].get("imported"):
        if args.require_gpu and not report["gpu"].get("cuda_available", False):
            report["errors"].append("CUDA is not available to torch.")
        elif args.require_gpu and report["gpu"].get("device_count", 0) == 0:
            report["errors"].append("No CUDA devices are visible to torch.")
        elif args.require_gpu and not report["gpu"].get("can_allocate", False):
            report["errors"].append("torch could not allocate a tensor on cuda:0.")

    hyper = report["hyperiqa_resnet_cache"]
    if hyper.get("checked") and not hyper.get("resnet50_cache_hits"):
        report["warnings"].append(
            "No cached ResNet-50 weights were found in common torch cache locations; "
            "offline HyperIQA visual-quality filtering may try to download them."
        )

    report["status"] = "blocked" if report["errors"] else "ready"
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Status: {report['status']}")
    print(f"Repo root: {report['repo_root']}")
    print(f"Input dir: {report['input_dir']}")
    print(f"Temp dir: {report['temp_dir']['path']}")
    tree = report["input_tree"]
    print(f"Input mp4 count: {tree['mp4_count']}")
    for binary in report["binaries"]:
        status = "found" if binary["found"] else "missing"
        detail = f" ({binary.get('first_line')})" if binary.get("first_line") else ""
        print(f"{binary['name']}: {status}{detail}")
    missing_sources = sum(1 for item in report["sources"] if not item["present"])
    print(f"Source anchors missing: {missing_sources}")
    if report["checkpoints"]["required"]:
        missing_ckpts = sum(1 for item in report["checkpoints"]["files"] if not item["present"])
        print(f"Checkpoint prerequisites missing: {missing_ckpts}")
    else:
        print("Checkpoint prerequisites: skipped for --cpu-only")
    if report["imports"]["checked"]:
        failed_imports = [m for m in report["imports"]["core_modules"] + report["imports"]["repo_modules"] if not m.get("imported")]
        print(f"Import failures: {len(failed_imports)}")
    if report["gpu"].get("checked"):
        print(
            "CUDA: "
            + f"available={report['gpu'].get('cuda_available')} "
            + f"devices={report['gpu'].get('device_count')} "
            + f"can_allocate={report['gpu'].get('can_allocate')}"
        )
    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    if report["errors"]:
        print("Errors:")
        for error in report["errors"]:
            print(f"  - {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight LatentSync data-preparation inputs and prerequisites.")
    parser.add_argument("--repo-root", type=str, default=".", help="LatentSync checkout to validate against.")
    parser.add_argument("--input-dir", type=str, required=True, help="Raw video tree to inspect.")
    parser.add_argument("--temp-dir", type=str, default="temp", help="Scratch directory the runner will use.")
    parser.add_argument("--cpu-only", action="store_true", help="Do not require GPU-stage auxiliary checkpoints.")
    parser.add_argument("--check-imports", action="store_true", help="Import critical Python packages and repo modules.")
    parser.add_argument("--strict-versions", action="store_true", help="Treat verified-baseline version mismatches as errors.")
    parser.add_argument("--require-gpu", action="store_true", help="Fail unless torch can see and allocate on CUDA.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text_report(report)
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

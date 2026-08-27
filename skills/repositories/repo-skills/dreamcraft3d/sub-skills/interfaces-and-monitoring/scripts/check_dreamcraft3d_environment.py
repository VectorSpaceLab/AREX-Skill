#!/usr/bin/env python3
"""Safe DreamCraft3D environment diagnostic.

This script performs read-only checks. It does not install packages, import heavy
ML libraries, download checkpoints, build Docker images, run containers, or start
DreamCraft3D training.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MIN_PYTHON = (3, 8)
DEFAULT_MIN_VRAM_GB = 20.0

REQUIRED_PATHS: Sequence[Tuple[str, str]] = (
    ("README.md", "file"),
    ("requirements.txt", "file"),
    ("launch.py", "file"),
    ("preprocess_image.py", "file"),
    ("gradio_app.py", "file"),
    ("docs/installation.md", "file"),
    ("docker/Dockerfile", "file"),
    ("docker/compose.yaml", "file"),
    ("configs/dreamcraft3d-coarse-nerf.yaml", "file"),
    ("configs/dreamcraft3d-coarse-neus.yaml", "file"),
    ("configs/dreamcraft3d-geometry.yaml", "file"),
    ("configs/dreamcraft3d-texture.yaml", "file"),
    ("threestudio", "dir"),
    ("load/zero123", "dir"),
    ("load/tets", "dir"),
)

OPTIONAL_GRADIO_CONFIGS: Sequence[str] = (
    "configs/gradio/dreamfusion-if.yaml",
    "configs/gradio/dreamfusion-sd.yaml",
    "configs/gradio/textmesh-if.yaml",
    "configs/gradio/fantasia3d.yaml",
    "configs/gradio/sjc.yaml",
    "configs/gradio/latentnerf.yaml",
)

MODEL_ARTIFACT_GROUPS: Sequence[Tuple[str, Sequence[str], str]] = (
    (
        "stable_zero123_checkpoint",
        ("load/zero123/stable_zero123.ckpt", "load/zero123/stable-zero123.ckpt"),
        "Stable Zero123 checkpoint; DreamCraft3D configs use the underscore form, while code defaults also mention the hyphen form.",
    ),
    (
        "stable_zero123_config",
        ("load/zero123/sd-objaverse-finetune-c_concat-256.yaml",),
        "Stable Zero123 config referenced by DreamCraft3D stage configs.",
    ),
    (
        "omnidata_depth_checkpoint",
        ("load/omnidata/omnidata_dpt_depth_v2.ckpt",),
        "Omnidata depth checkpoint used by preprocess_image.py.",
    ),
    (
        "omnidata_normal_checkpoint",
        ("load/omnidata/omnidata_dpt_normal_v2.ckpt",),
        "Omnidata normal checkpoint used by preprocess_image.py.",
    ),
    (
        "dmtet_grids",
        ("load/tets/32_tets.npz", "load/tets/64_tets.npz", "load/tets/128_tets.npz"),
        "DMTet grid files used by geometry/texture stages.",
    ),
)

PACKAGE_PROBES: Sequence[Tuple[str, str, Sequence[str]]] = (
    ("torch", "torch", ("torch",)),
    ("torchvision", "torchvision", ("torchvision",)),
    ("pytorch_lightning", "pytorch_lightning", ("lightning", "pytorch-lightning")),
    ("omegaconf", "omegaconf", ("omegaconf",)),
    ("gradio", "gradio", ("gradio",)),
    ("psutil", "psutil", ("psutil",)),
    ("trimesh", "trimesh", ("trimesh",)),
    ("cv2", "opencv-python", ("opencv-python",)),
    ("diffusers", "diffusers", ("diffusers",)),
    ("transformers", "transformers", ("transformers",)),
    ("accelerate", "accelerate", ("accelerate",)),
    ("xformers", "xformers", ("xformers",)),
    ("bitsandbytes", "bitsandbytes", ("bitsandbytes",)),
    ("nvdiffrast", "nvdiffrast", ("nvdiffrast",)),
    ("tinycudann", "tiny-cuda-nn/tinycudann", ("tiny-cuda-nn", "tinycudann")),
    ("nerfacc", "nerfacc", ("nerfacc",)),
    ("ninja", "ninja", ("ninja",)),
    ("einops", "einops", ("einops",)),
    ("kornia", "kornia", ("kornia",)),
    ("controlnet_aux", "controlnet_aux", ("controlnet-aux", "controlnet_aux")),
)


def status_record(name: str, status: str, detail: str, **data: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {"name": name, "status": status, "detail": detail}
    if data:
        record["data"] = data
    return record


def run_command(cmd: Sequence[str], timeout: int = 5) -> Tuple[Optional[int], str, str]:
    try:
        proc = subprocess.run(
            list(cmd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return None, "", f"executable not found: {cmd[0]}"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return None, stdout, (stderr + "\ncommand timed out").strip()
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check_python() -> Dict[str, Any]:
    version_tuple = sys.version_info[:3]
    status = "ok" if version_tuple >= MIN_PYTHON else "fail"
    detail = (
        f"Python {platform.python_version()} detected; DreamCraft3D expects >= "
        f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}."
    )
    return status_record(
        "python_version",
        status,
        detail,
        version=platform.python_version(),
        implementation=platform.python_implementation(),
        platform=platform.platform(),
    )


def check_repo_root(repo_root: Path) -> Dict[str, Any]:
    if not repo_root.exists():
        return status_record("repo_root", "fail", "repo root does not exist")
    if not repo_root.is_dir():
        return status_record("repo_root", "fail", "repo root is not a directory")
    return status_record("repo_root", "ok", "repo root exists")


def check_required_paths(repo_root: Path) -> Dict[str, Any]:
    missing: List[str] = []
    wrong_type: List[str] = []
    present: List[str] = []
    for rel, expected_type in REQUIRED_PATHS:
        path = repo_root / rel
        if not path.exists():
            missing.append(rel)
        elif expected_type == "file" and not path.is_file():
            wrong_type.append(rel)
        elif expected_type == "dir" and not path.is_dir():
            wrong_type.append(rel)
        else:
            present.append(rel)

    if missing or wrong_type:
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if wrong_type:
            parts.append(f"wrong type: {', '.join(wrong_type)}")
        return status_record(
            "required_repo_paths",
            "fail",
            "; ".join(parts),
            present=present,
            missing=missing,
            wrong_type=wrong_type,
        )
    return status_record(
        "required_repo_paths",
        "ok",
        "all required DreamCraft3D repo-relative files and directories are present",
        present=present,
    )


def check_gradio_configs(repo_root: Path) -> Dict[str, Any]:
    present = [rel for rel in OPTIONAL_GRADIO_CONFIGS if (repo_root / rel).is_file()]
    missing = [rel for rel in OPTIONAL_GRADIO_CONFIGS if not (repo_root / rel).is_file()]
    if missing:
        return status_record(
            "gradio_demo_configs",
            "warn",
            "gradio_app.py references configs/gradio/*.yaml; missing files can block the generic UI launch",
            present=present,
            missing=missing,
        )
    return status_record(
        "gradio_demo_configs",
        "ok",
        "all gradio demo config files referenced by gradio_app.py are present",
        present=present,
    )


def check_model_artifacts(repo_root: Path, enabled: bool) -> Dict[str, Any]:
    if not enabled:
        return status_record(
            "model_artifacts",
            "skip",
            "model artifact checks skipped; pass --check-model-paths to enable local file checks",
        )

    groups: List[Dict[str, Any]] = []
    any_missing_required_group = False
    for name, alternatives, note in MODEL_ARTIFACT_GROUPS:
        present = [rel for rel in alternatives if (repo_root / rel).exists()]
        missing = [rel for rel in alternatives if not (repo_root / rel).exists()]
        if name == "dmtet_grids":
            ok = len(present) == len(alternatives)
        else:
            ok = len(present) > 0
        if not ok:
            any_missing_required_group = True
        groups.append(
            {
                "name": name,
                "status": "ok" if ok else "warn",
                "present": present,
                "missing": missing,
                "note": note,
            }
        )

    status = "warn" if any_missing_required_group else "ok"
    detail = (
        "some local model/artifact paths are missing"
        if any_missing_required_group
        else "local model/artifact paths checked successfully"
    )
    return status_record("model_artifacts", status, detail, groups=groups)


def parse_nvidia_smi_csv(stdout: str) -> List[Dict[str, Any]]:
    gpus: List[Dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue
        index, name, total_mib, free_mib, driver = parts[:5]
        def to_float(value: str) -> Optional[float]:
            try:
                return float(value)
            except ValueError:
                return None
        total = to_float(total_mib)
        free = to_float(free_mib)
        item: Dict[str, Any] = {"index": index, "name": name, "driver_version": driver}
        if total is not None:
            item["memory_total_gb"] = round(total / 1024.0, 2)
        if free is not None:
            item["memory_free_gb"] = round(free / 1024.0, 2)
        gpus.append(item)
    return gpus


def check_nvidia_smi(min_vram_gb: float) -> Dict[str, Any]:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return status_record(
            "nvidia_smi",
            "warn",
            "nvidia-smi was not found; full DreamCraft3D training requires an NVIDIA CUDA GPU",
        )
    code, stdout, stderr = run_command(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits",
        ],
        timeout=5,
    )
    if code != 0:
        return status_record(
            "nvidia_smi",
            "warn",
            "nvidia-smi command failed",
            returncode=code,
            stderr=stderr,
        )
    gpus = parse_nvidia_smi_csv(stdout)
    if not gpus:
        return status_record(
            "nvidia_smi",
            "warn",
            "nvidia-smi ran but no GPUs were parsed from its output",
            raw_output=stdout,
        )
    enough = [gpu for gpu in gpus if gpu.get("memory_total_gb", 0.0) >= min_vram_gb]
    status = "ok" if enough else "warn"
    detail = (
        f"{len(enough)} visible GPU(s) meet the {min_vram_gb:g}GB default-run guidance"
        if enough
        else f"visible GPU(s) are below the {min_vram_gb:g}GB default-run guidance"
    )
    return status_record("nvidia_smi", status, detail, gpus=gpus)


def check_docker() -> Dict[str, Any]:
    docker_path = shutil.which("docker")
    if docker_path is None:
        return status_record(
            "docker",
            "warn",
            "docker executable was not found; Docker route is unavailable until the host is prepared",
        )

    docker_code, docker_stdout, docker_stderr = run_command(["docker", "--version"], timeout=5)
    compose_code, compose_stdout, compose_stderr = run_command(
        ["docker", "compose", "version"], timeout=5
    )
    status = "ok" if docker_code == 0 and compose_code == 0 else "warn"
    detail = (
        "docker and docker compose executables responded"
        if status == "ok"
        else "docker executable exists, but version probes did not both succeed"
    )
    return status_record(
        "docker",
        status,
        detail,
        docker_version=docker_stdout,
        docker_stderr=docker_stderr,
        compose_version=compose_stdout,
        compose_stderr=compose_stderr,
    )


def safe_find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def metadata_version(candidates: Iterable[str]) -> Optional[str]:
    for dist_name in candidates:
        try:
            return importlib.metadata.version(dist_name)
        except importlib.metadata.PackageNotFoundError:
            continue
        except Exception:
            continue
    return None


def check_packages() -> Dict[str, Any]:
    packages: List[Dict[str, Any]] = []
    missing_core: List[str] = []
    core_modules = {"torch", "pytorch_lightning", "omegaconf"}
    for module_name, display_name, dist_candidates in PACKAGE_PROBES:
        available = safe_find_spec(module_name)
        version = metadata_version(dist_candidates)
        item = {
            "module": module_name,
            "display_name": display_name,
            "available_by_find_spec": available,
            "metadata_version": version,
        }
        packages.append(item)
        if module_name in core_modules and not available:
            missing_core.append(module_name)

    if missing_core:
        status = "warn"
        detail = "core Python packages for launch/config inspection are not all discoverable"
    else:
        status = "ok"
        detail = "core Python packages are discoverable by safe spec probes"
    return status_record(
        "python_package_probes",
        status,
        detail,
        probe_method="importlib.util.find_spec plus importlib.metadata; packages were not imported",
        packages=packages,
        missing_core=missing_core,
    )


def check_environment_variables() -> Dict[str, Any]:
    vars_to_check = ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES")
    values = {name: os.environ.get(name) for name in vars_to_check if os.environ.get(name)}
    if "CUDA_VISIBLE_DEVICES" in values:
        return status_record(
            "environment_variables",
            "warn",
            "CUDA_VISIBLE_DEVICES is set; launch.py will ignore --gpu and use the visible devices",
            values=values,
        )
    if values:
        return status_record(
            "environment_variables",
            "ok",
            "GPU-related environment variables detected",
            values=values,
        )
    return status_record(
        "environment_variables",
        "ok",
        "no CUDA visibility override detected in common environment variables",
    )


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = Path(args.repo_root).expanduser().resolve()
    checks: List[Dict[str, Any]] = [
        check_python(),
        check_repo_root(repo_root),
    ]
    if repo_root.exists() and repo_root.is_dir():
        checks.extend(
            [
                check_required_paths(repo_root),
                check_gradio_configs(repo_root),
                check_model_artifacts(repo_root, args.check_model_paths),
            ]
        )
    checks.extend(
        [
            check_nvidia_smi(args.min_vram_gb),
            check_docker(),
            check_packages(),
            check_environment_variables(),
        ]
    )

    counts: Dict[str, int] = {}
    for check in checks:
        counts[check["status"]] = counts.get(check["status"], 0) + 1

    return {
        "tool": "check_dreamcraft3d_environment",
        "repo_root_argument": args.repo_root,
        "min_vram_gb": args.min_vram_gb,
        "checks": checks,
        "summary": counts,
        "notes": [
            "This diagnostic is read-only and does not import heavy ML packages.",
            "Warnings for CUDA, Docker, or model artifacts usually block full DreamCraft3D runs but may still allow static skill/useability checks.",
        ],
    }


def print_text(report: Dict[str, Any]) -> None:
    print("DreamCraft3D environment diagnostic")
    print(f"repo root argument: {report['repo_root_argument']}")
    print(f"default-run VRAM guidance: {report['min_vram_gb']:g}GB")
    print("")
    for check in report["checks"]:
        print(f"[{check['status'].upper()}] {check['name']}: {check['detail']}")
        data = check.get("data", {})
        if check["name"] == "nvidia_smi" and data.get("gpus"):
            for gpu in data["gpus"]:
                total = gpu.get("memory_total_gb", "?")
                free = gpu.get("memory_free_gb", "?")
                print(
                    f"  - GPU {gpu.get('index')}: {gpu.get('name')} "
                    f"total={total}GB free={free}GB driver={gpu.get('driver_version')}"
                )
        elif check["name"] == "required_repo_paths":
            missing = data.get("missing") or []
            wrong_type = data.get("wrong_type") or []
            if missing:
                print(f"  missing: {', '.join(missing)}")
            if wrong_type:
                print(f"  wrong type: {', '.join(wrong_type)}")
        elif check["name"] == "gradio_demo_configs":
            missing = data.get("missing") or []
            if missing:
                shown = ", ".join(missing[:4])
                suffix = " ..." if len(missing) > 4 else ""
                print(f"  missing gradio configs: {shown}{suffix}")
        elif check["name"] == "model_artifacts" and data.get("groups"):
            for group in data["groups"]:
                present = group.get("present") or []
                missing = group.get("missing") or []
                print(
                    f"  - {group['name']}: {group['status']} "
                    f"present={len(present)} missing={len(missing)}"
                )
        elif check["name"] == "docker":
            if data.get("docker_version"):
                print(f"  docker: {data['docker_version']}")
            if data.get("compose_version"):
                print(f"  compose: {data['compose_version']}")
        elif check["name"] == "python_package_probes":
            missing_core = data.get("missing_core") or []
            if missing_core:
                print(f"  missing core modules: {', '.join(missing_core)}")
            available = [
                item["module"]
                for item in data.get("packages", [])
                if item.get("available_by_find_spec")
            ]
            if available:
                print(f"  discoverable modules: {', '.join(available[:12])}" + (" ..." if len(available) > 12 else ""))
        elif check["name"] == "environment_variables" and data.get("values"):
            for key, value in data["values"].items():
                print(f"  {key}={value}")
    print("")
    print("Summary:", ", ".join(f"{k}={v}" for k, v in sorted(report["summary"].items())))
    for note in report["notes"]:
        print(f"Note: {note}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only DreamCraft3D environment checker")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a DreamCraft3D checkout; defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report.",
    )
    parser.add_argument(
        "--check-model-paths",
        action="store_true",
        help="Check local model/artifact paths such as Zero123, Omnidata, and DMTet files.",
    )
    parser.add_argument(
        "--min-vram-gb",
        type=float,
        default=DEFAULT_MIN_VRAM_GB,
        help="VRAM threshold for default-run guidance; defaults to 20GB.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

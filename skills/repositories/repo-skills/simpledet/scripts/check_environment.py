#!/usr/bin/env python3
"""Report SimpleDet environment status without installing, downloading, killing, or training."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

EXT_SUFFIXES = {".so", ".pyd", ".dylib"}

PROBE_GROUPS = [
    (
        "foundation",
        [
            ("mxnet", True, "legacy runtime backend"),
            ("numpy", True, "array operations"),
            ("cv2", True, "image IO"),
            ("pytz", True, "documented dependency"),
            ("pycocotools", True, "patched cocoapi dependency"),
            ("mxnext", True, "symbolic helper dependency"),
        ],
    ),
    (
        "runtime",
        [
            ("operator_py.cython.bbox", True, "anchor overlap Cython module"),
            ("operator_py.cython.cpu_nms", True, "CPU NMS Cython module"),
            ("operator_py.nms", True, "Python NMS wrapper"),
            ("core.detection_input", True, "data pipeline and anchor loader"),
            ("detection_train", True, "training entry point"),
            ("detection_test", True, "evaluation entry point"),
            ("detection_infer_speed", True, "speed benchmark entry point"),
            ("mask_test", True, "mask evaluation entry point"),
            ("config.faster_r50v1_fpn_1x", True, "representative config import"),
        ],
    ),
    (
        "optional",
        [
            ("operator_py.cython.bbox_self", False, "CrowdHuman / ignore-anchor path"),
            ("operator_py.cython.gpu_nms", False, "CUDA-backed NMS extension"),
            ("mxboard", False, "TensorBoard logging helper"),
            ("tensorboard", False, "TensorBoard UI"),
        ],
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely probe a SimpleDet checkout for Python, import, backend, and "
            "extension readiness."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the SimpleDet repository root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 if any required probe fails.",
    )
    return parser.parse_args()


def resolve_repo_root(raw_root: str) -> Path:
    repo_root = Path(raw_root).expanduser().resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"repo root does not exist: {repo_root}")
    return repo_root


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except UnicodeDecodeError:
        return None


def extract_make_targets(makefile_text: str) -> Dict[str, List[str]]:
    targets: Dict[str, List[str]] = {}
    lines = makefile_text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("all:") or line.startswith("clean:"):
            name = line.split(":", 1)[0].strip()
            body: List[str] = []
            for follow in lines[idx + 1 :]:
                if follow.startswith("\t"):
                    body.append(follow.strip())
                elif follow.strip() == "":
                    continue
                else:
                    break
            targets[name] = body
    return targets


def list_extension_artifacts(repo_root: Path, simple_name: str) -> List[str]:
    ext_dir = repo_root / "operator_py" / "cython"
    if not ext_dir.exists():
        return []
    artifacts: List[str] = []
    for candidate in sorted(ext_dir.iterdir()):
        if not candidate.is_file():
            continue
        if candidate.suffix not in EXT_SUFFIXES:
            continue
        if candidate.name.startswith(simple_name):
            artifacts.append(str(candidate.relative_to(repo_root)))
    return artifacts


def probe_module(module_name: str, required: bool, note: str, repo_root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "module": module_name,
        "required": required,
        "note": note,
    }

    simple_name = module_name.rsplit(".", 1)[-1]
    if module_name.startswith("operator_py.cython."):
        artifacts = list_extension_artifacts(repo_root, simple_name)
        result["localArtifacts"] = artifacts
        if not artifacts:
            result["localArtifacts"] = []

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        result["status"] = "missing"
        result["message"] = str(exc)
        if module_name.startswith("operator_py.cython.") and not result.get("localArtifacts"):
            result["message"] = (
                f"no compiled artifact found under operator_py/cython/; {exc}"
            )
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["status"] = "error"
        result["message"] = f"{type(exc).__name__}: {exc}"
    else:
        result["status"] = "ok"
        result["file"] = getattr(module, "__file__", None)
        if result["file"]:
            module_path = Path(result["file"]).resolve()
            result["source"] = "local" if is_within(module_path, repo_root) else "external"
        if module_name == "mxnet":
            try:
                result["num_gpus"] = int(module.context.num_gpus())
            except Exception as exc:  # pragma: no cover - diagnostic path
                result["num_gpusError"] = f"{type(exc).__name__}: {exc}"
        if module_name.startswith("operator_py.cython.") and not result.get("localArtifacts"):
            result["message"] = "import succeeded, but no local compiled artifact was found"
    return result


def inspect_backend(repo_root: Path) -> Dict[str, Any]:
    cuda_home = os.environ.get("CUDAHOME") or os.environ.get("CUDA_HOME")
    nvcc = shutil.which("nvcc")
    cuda_nvcc = None
    if cuda_home:
        candidate = Path(cuda_home).expanduser() / "bin" / "nvcc"
        cuda_nvcc = str(candidate) if candidate.exists() else None
    return {
        "CUDAHOME": cuda_home,
        "nvcc": nvcc,
        "cudaHomeNvcc": cuda_nvcc,
        "compiledArtifacts": list_compiled_artifacts(repo_root),
    }


def list_compiled_artifacts(repo_root: Path) -> List[str]:
    ext_dir = repo_root / "operator_py" / "cython"
    if not ext_dir.exists():
        return []
    artifacts: List[str] = []
    for candidate in sorted(ext_dir.iterdir()):
        if candidate.is_file() and candidate.suffix in EXT_SUFFIXES:
            artifacts.append(str(candidate.relative_to(repo_root)))
    return artifacts


def inspect_repo(repo_root: Path) -> Dict[str, Any]:
    makefile = repo_root / "Makefile"
    setup_py = repo_root / "setup.py"
    pyproject = repo_root / "pyproject.toml"
    makefile_text = read_text(makefile)
    targets = extract_make_targets(makefile_text) if makefile_text else {}
    return {
        "makefile": {
            "present": makefile.exists(),
            "targets": targets,
        },
        "packageMetadata": {
            "setupPy": setup_py.exists(),
            "pyprojectToml": pyproject.exists(),
        },
        "operatorSetup": {
            "present": (repo_root / "operator_py" / "cython" / "setup.py").exists(),
        },
    }


def build_report(repo_root: Path) -> Dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    report: Dict[str, Any] = {
        "repoRoot": str(repo_root),
        "cwd": str(Path.cwd().resolve()),
        "python": {
            "executable": sys.executable,
            "version": sys.version.replace("\n", " "),
            "platform": platform.platform(),
        },
        "repo": inspect_repo(repo_root),
        "backend": inspect_backend(repo_root),
        "groups": [],
    }

    all_probes: List[Dict[str, Any]] = []
    groups_out: List[Dict[str, Any]] = []
    for group_name, probes in PROBE_GROUPS:
        group_out: Dict[str, Any] = {"name": group_name, "probes": []}
        for module_name, required, note in probes:
            probe = probe_module(module_name, required, note, repo_root)
            group_out["probes"].append(probe)
            all_probes.append(probe)
        groups_out.append(group_out)

    report["groups"] = groups_out
    report["summary"] = summarize(report, all_probes)
    return report


def summarize(report: Dict[str, Any], probes: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    probes_list = list(probes)
    required = [probe for probe in probes_list if probe.get("required")]
    optional = [probe for probe in probes_list if not probe.get("required")]
    required_ok = all(probe.get("status") == "ok" for probe in required)
    optional_ok = all(probe.get("status") in {"ok", "missing"} for probe in optional)
    backend = report["backend"]
    cuda_ready = bool(backend.get("nvcc") or backend.get("cudaHomeNvcc"))
    return {
        "requiredOk": required_ok,
        "optionalOk": optional_ok,
        "cudaToolkitVisible": cuda_ready,
        "requiredFailures": [
            {
                "module": probe["module"],
                "status": probe.get("status"),
                "message": probe.get("message"),
            }
            for probe in required
            if probe.get("status") != "ok"
        ],
    }


def render_text(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("SimpleDet environment check")
    lines.append(f"repo root: {report['repoRoot']}")
    lines.append(f"cwd: {report['cwd']}")
    lines.append(
        f"python: {report['python']['version']}"
    )
    lines.append(f"executable: {report['python']['executable']}")
    lines.append(f"platform: {report['python']['platform']}")

    repo = report["repo"]
    make_targets = repo["makefile"]["targets"]
    lines.append(
        "package metadata: "
        + ("absent" if not repo["packageMetadata"]["setupPy"] and not repo["packageMetadata"]["pyprojectToml"] else "present")
    )
    lines.append(
        "operator_py/cython/setup.py: "
        + ("present" if repo["operatorSetup"]["present"] else "missing")
    )
    if make_targets.get("all"):
        lines.append("make all target:")
        for step in make_targets["all"]:
            lines.append(f"  - {step}")
    else:
        lines.append("make all target: not found")

    backend = report["backend"]
    lines.append("backend:")
    lines.append(f"  CUDAHOME: {backend.get('CUDAHOME') or 'unset'}")
    lines.append(f"  nvcc: {backend.get('nvcc') or 'missing'}")
    lines.append(f"  CUDAHOME/bin/nvcc: {backend.get('cudaHomeNvcc') or 'missing'}")
    artifacts = backend.get("compiledArtifacts", [])
    if artifacts:
        lines.append("  compiled artifacts:")
        for item in artifacts:
            lines.append(f"    - {item}")
    else:
        lines.append("  compiled artifacts: none found")

    lines.append("imports:")
    for group in report["groups"]:
        lines.append(f"  {group['name']}:")
        for probe in group["probes"]:
            status = probe.get("status", "unknown")
            marker = "OK" if status == "ok" else status.upper()
            suffix_parts: List[str] = []
            if probe.get("source"):
                suffix_parts.append(f"source={probe['source']}")
            if probe.get("file"):
                suffix_parts.append(f"file={probe['file']}")
            if probe.get("num_gpus") is not None:
                suffix_parts.append(f"num_gpus={probe['num_gpus']}")
            if probe.get("message"):
                suffix_parts.append(str(probe["message"]))
            suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
            req = "required" if probe.get("required") else "optional"
            lines.append(f"    - [{req}] {probe['module']}: {marker}{suffix}")

    summary = report["summary"]
    lines.append("summary:")
    lines.append(f"  required ok: {summary['requiredOk']}")
    lines.append(f"  optional ok: {summary['optionalOk']}")
    lines.append(f"  CUDA toolkit visible: {summary['cudaToolkitVisible']}")
    if summary["requiredFailures"]:
        lines.append("  required failures:")
        for failure in summary["requiredFailures"]:
            lines.append(
                f"    - {failure['module']}: {failure['status']}"
                + (f" ({failure['message']})" if failure.get("message") else "")
            )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        repo_root = resolve_repo_root(args.repo_root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = build_report(repo_root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.strict and not report["summary"]["requiredOk"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

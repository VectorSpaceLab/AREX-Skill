#!/usr/bin/env python3
"""Check an installed HLoc environment without running model inference.

The helper is safe by default: it imports public modules, reports package and
backend versions, lists available configuration names, and can optionally check
that core CLI parsers are importable. It does not download weights, read image
datasets, write feature files, run COLMAP, or mutate the environment.

Examples:
  python scripts/check_hloc_environment.py
  python scripts/check_hloc_environment.py --json --check-cli
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, List

CORE_MODULES = [
    "hloc",
    "hloc.extract_features",
    "hloc.match_features",
    "hloc.match_dense",
    "hloc.pairs_from_retrieval",
    "hloc.pairs_from_exhaustive",
    "hloc.reconstruction",
    "hloc.triangulation",
    "hloc.localize_sfm",
    "hloc.localize_inloc",
]

CLI_MODULES = [
    "hloc.extract_features",
    "hloc.match_features",
    "hloc.pairs_from_exhaustive",
    "hloc.pairs_from_retrieval",
    "hloc.reconstruction",
    "hloc.localize_sfm",
]


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic output path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}


def collect_configs() -> Dict[str, List[str]]:
    configs: Dict[str, List[str]] = {}
    try:
        from hloc import extract_features, match_dense, match_features

        configs["extract_features"] = sorted(extract_features.confs.keys())
        configs["match_features"] = sorted(match_features.confs.keys())
        configs["match_dense"] = sorted(match_dense.confs.keys())
    except Exception as exc:  # pragma: no cover - diagnostic output path
        configs["error"] = [f"{type(exc).__name__}: {exc}"]
    return configs


def collect_versions() -> Dict[str, Any]:
    names = ["hloc", "pycolmap", "torch", "torchvision", "opencv-python", "h5py", "kornia", "lightglue"]
    versions: Dict[str, Any] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    try:
        import hloc

        versions["hloc_import_version"] = getattr(hloc, "__version__", None)
    except Exception as exc:  # pragma: no cover
        versions["hloc_import_error"] = f"{type(exc).__name__}: {exc}"
    return versions


def collect_backend() -> Dict[str, Any]:
    backend: Dict[str, Any] = {"torch_imported": False, "cuda_required_by_hloc": False}
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        backend["torch_error"] = f"{type(exc).__name__}: {exc}"
        return backend
    backend.update(
        {
            "torch_imported": True,
            "torch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    if torch.cuda.is_available():
        try:
            backend["cuda_device0"] = torch.cuda.get_device_name(0)
            backend["cuda_capability0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:  # pragma: no cover
            backend["cuda_query_error"] = f"{type(exc).__name__}: {exc}"
    return backend


def check_cli_help(timeout: float) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for module in CLI_MODULES:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", module, "--help"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except Exception as exc:  # pragma: no cover
            results.append({"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            continue
        results.append(
            {
                "module": module,
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "first_stdout_line": (proc.stdout.splitlines() or [""])[0],
                "stderr_excerpt": proc.stderr[:300],
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe `python -m hloc.* --help` parser checks.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds per CLI help check; default: %(default)s.")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "versions": collect_versions(),
        "imports": [import_status(name) for name in CORE_MODULES],
        "configs": collect_configs(),
        "backend": collect_backend(),
    }
    if args.check_cli:
        report["cli_help"] = check_cli_help(args.timeout)

    failed_imports = [item for item in report["imports"] if not item["ok"]]
    failed_cli = [item for item in report.get("cli_help", []) if not item["ok"]]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Versions:")
        for key, value in report["versions"].items():
            print(f"  {key}: {value}")
        print("Imports:")
        for item in report["imports"]:
            marker = "ok" if item["ok"] else "FAIL"
            suffix = "" if item["ok"] else f" ({item['error']})"
            print(f"  {marker}: {item['name']}{suffix}")
        print("Configs:")
        for key, values in report["configs"].items():
            print(f"  {key}: {', '.join(values)}")
        print("Backend:")
        for key, value in report["backend"].items():
            print(f"  {key}: {value}")
        if args.check_cli:
            print("CLI help:")
            for item in report["cli_help"]:
                marker = "ok" if item["ok"] else "FAIL"
                print(f"  {marker}: {item['module']} -> {item.get('first_stdout_line', item.get('error', ''))}")

    return 1 if failed_imports or failed_cli else 0


if __name__ == "__main__":
    raise SystemExit(main())

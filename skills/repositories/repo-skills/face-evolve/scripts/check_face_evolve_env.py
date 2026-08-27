#!/usr/bin/env python3
"""Check dependencies and optional source-layout sanity for face.evoLVe tasks."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Dict, List

CHECK_MODULES = {
    "core": ["numpy", "PIL", "cv2", "tqdm"],
    "torch": ["torch", "torchvision", "scipy", "sklearn", "matplotlib", "tensorboardX", "bcolz"],
    "paddle": ["paddle", "paddleslim"],
    "data": ["numpy", "bcolz"],
}


def import_status(module_name: str) -> Dict[str, object]:
    try:
        module = importlib.import_module(module_name)
        return {
            "ok": True,
            "version": getattr(module, "__version__", "unknown"),
            "file": None,
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def inspect_repo_root(repo_root: Path) -> Dict[str, object]:
    repo_root = repo_root.expanduser().resolve()
    result: Dict[str, object] = {"path_supplied": str(repo_root), "ok": True, "issues": []}
    issues: List[str] = result["issues"]  # type: ignore[assignment]
    expected = ["backbone", "head", "loss", "util", "applications/align", "paddle"]
    if not repo_root.exists() or not repo_root.is_dir():
        result["ok"] = False
        issues.append("repo root does not exist or is not a directory")
        return result
    for rel in expected:
        if not (repo_root / rel).exists():
            result["ok"] = False
            issues.append(f"missing expected path: {rel}")
    if (repo_root / "paddle" / "__init__.py").exists():
        issues.append("top-level paddle/ can shadow installed PaddlePaddle if repo root is placed on PYTHONPATH")
    for weight in ["pnet.npy", "rnet.npy", "onet.npy"]:
        if not (repo_root / "applications" / "align" / weight).is_file():
            issues.append(f"alignment weight missing: applications/align/{weight}")
    if not any((repo_root / name).exists() for name in ["pyproject.toml", "setup.py", "setup.cfg"]):
        issues.append("source checkout has no standard Python package metadata")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check face.evoLVe workflow dependencies and optional checkout layout.")
    parser.add_argument("--check", action="append", choices=sorted(CHECK_MODULES), default=[], help="Dependency group to check; may be repeated. Defaults to core, torch, paddle, data.")
    parser.add_argument("--repo-root", help="Optional target face.evoLVe checkout to inspect for expected source paths.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    groups = args.check or ["core", "torch", "paddle", "data"]
    modules = []
    for group in groups:
        modules.extend(CHECK_MODULES[group])
    modules = sorted(set(modules))

    report = {
        "schema": "face-evolve-env-check-v1",
        "groups": groups,
        "python": sys.version.split()[0],
        "modules": {name: import_status(name) for name in modules},
        "repo_root": inspect_repo_root(Path(args.repo_root)) if args.repo_root else None,
    }

    ok = all(item.get("ok") for item in report["modules"].values())
    if report["repo_root"] is not None:
        ok = ok and bool(report["repo_root"].get("ok"))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("face.evoLVe environment check: {}".format("OK" if ok else "ISSUES"))
        print("Python:", report["python"])
        for name, status in report["modules"].items():
            if status.get("ok"):
                print(f"- {name}: ok ({status.get('version')})")
            else:
                print(f"- {name}: FAIL ({status.get('error')})")
        if report["repo_root"] is not None:
            root = report["repo_root"]
            print("Repo root:", "ok" if root.get("ok") else "issues")
            for issue in root.get("issues", []):
                print("  -", issue)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check whether a Python environment can import VGen and see required backends."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List


REQUIRED_IMPORTS = [
    "torch",
    "torchvision",
    "cv2",
    "numpy",
    "easydict",
    "einops",
    "open_clip",
    "fairscale",
    "diffusers",
    "transformers",
    "piq",
    "skimage",
]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check VGen importability, CUDA readiness, and common video-generation dependencies.",
        allow_abbrev=False,
    )
    parser.add_argument("--repo-root", type=Path, default=Path('.'), help="VGen checkout root to add to sys.path.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is not available and cannot allocate a tensor.")
    parser.add_argument("--skip-tools", action="store_true", help="Skip importing the heavy VGen tools package.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of human-readable text.")
    return parser.parse_args(argv)


def try_import(name: str) -> Dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"name": name, "ok": False, "error": str(exc)}
    version = getattr(module, "__version__", None)
    return {"name": name, "ok": True, "version": version}


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    report: Dict[str, object] = {
        "repo_root_has_expected_files": (repo_root / "tools").is_dir() and (repo_root / "utils").is_dir(),
        "ffmpeg_on_path": shutil.which("ffmpeg") is not None,
        "imports": [],
        "cuda": {"available": False, "allocation": False},
        "tools_import": None,
    }

    sys.path.insert(0, str(repo_root))

    import_results = [try_import(name) for name in REQUIRED_IMPORTS]
    report["imports"] = import_results

    torch_result = next((item for item in import_results if item["name"] == "torch" and item["ok"]), None)
    if torch_result:
        import torch

        available = bool(torch.cuda.is_available())
        report["cuda"] = {"available": available, "allocation": False, "device_count": torch.cuda.device_count()}
        if available:
            try:
                tensor = torch.randn(1, device="cuda")
                report["cuda"]["allocation"] = True
                report["cuda"]["sample"] = float(tensor.item())
            except Exception as exc:
                report["cuda"]["error"] = str(exc)

    if not args.skip_tools:
        try:
            import tools  # noqa: F401 - registers VGen modules
            report["tools_import"] = {"ok": True}
        except Exception as exc:
            report["tools_import"] = {"ok": False, "error": str(exc)}

    failed_imports = [item for item in import_results if not item["ok"]]
    success = True
    if not report["repo_root_has_expected_files"]:
        success = False
    if failed_imports:
        success = False
    if args.require_cuda and not report["cuda"].get("allocation"):
        success = False
    if report["tools_import"] and not report["tools_import"].get("ok"):
        success = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Repo root shape: {'ok' if report['repo_root_has_expected_files'] else 'missing tools/ or utils/'}")
        print(f"ffmpeg on PATH: {report['ffmpeg_on_path']}")
        for item in import_results:
            if item["ok"]:
                version = item.get("version") or "unknown"
                print(f"import {item['name']}: ok ({version})")
            else:
                print(f"import {item['name']}: FAIL ({item['error']})")
        cuda = report["cuda"]
        print(f"CUDA available: {cuda.get('available')} allocation: {cuda.get('allocation')} devices: {cuda.get('device_count', 0)}")
        if report["tools_import"] is not None:
            if report["tools_import"].get("ok"):
                print("import tools: ok")
            else:
                print(f"import tools: FAIL ({report['tools_import']['error']})")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

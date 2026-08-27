#!/usr/bin/env python3
"""Check Pyramid-Flow runtime imports and bundled helper scripts."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_IMPORTS: list[tuple[str, str]] = [
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("transformers", "transformers"),
    ("accelerate", "accelerate"),
    ("diffusers", "diffusers"),
    ("einops", "einops"),
    ("jsonlines", "jsonlines"),
    ("tiktoken", "tiktoken"),
    ("contexttimer", "contexttimer"),
    ("sentencepiece", "sentencepiece"),
    ("cv2", "opencv-python-headless"),
    ("imageio", "imageio"),
    ("tensorboardX", "tensorboardX"),
    ("safetensors", "safetensors"),
    ("huggingface_hub", "huggingface_hub"),
]

OPTIONAL_IMPORTS: list[tuple[str, str]] = [
    ("spacy", "spacy"),
    ("streamlit", "streamlit"),
    ("plotly", "plotly"),
    ("pandas", "pandas"),
    ("magic", "python-magic"),
]

REPO_IMPORTS = ["pyramid_dit", "video_vae", "dataset", "diffusion_schedulers", "trainer_misc"]
HELPER_SCRIPTS = [
    "sub-skills/core-components/scripts/smoke_core_components.py",
    "sub-skills/generation-inference/scripts/check_generation_prereqs.py",
    "sub-skills/generation-inference/scripts/run_generation.py",
    "sub-skills/data-preparation/scripts/check_dataset_fixtures.py",
    "sub-skills/data-preparation/scripts/build_precompute_commands.py",
    "sub-skills/training-workflows/scripts/check_training_prereqs.py",
    "sub-skills/training-workflows/scripts/build_training_commands.py",
]


def _module_status(import_name: str, dist_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # pragma: no cover - import failures are environment-specific
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(dist_name)
        except Exception:
            version = None

    status: dict[str, Any] = {"ok": True, "version": version}
    if import_name == "torch":
        import torch

        status["cuda_available"] = torch.cuda.is_available()
        status["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
        status["torch_cuda_version"] = getattr(torch.version, "cuda", None)
        status["distributed_available"] = torch.distributed.is_available()
        mps_backend = getattr(torch.backends, "mps", None)
        status["mps_available"] = bool(mps_backend) and torch.backends.mps.is_available()
    return status


def _script_help_status(script_relpath: str, timeout: int) -> dict[str, Any]:
    script_path = SKILL_ROOT / script_relpath
    if not script_path.exists():
        return {"ok": False, "error": f"missing script: {script_relpath}"}

    try:
        completed = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=str(SKILL_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - subprocess failures are environment-specific
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_head": completed.stdout.splitlines()[:12],
        "stderr_head": completed.stderr.splitlines()[:12],
    }


def _repo_import_status(repo_root: Path) -> dict[str, Any]:
    if not repo_root.exists():
        return {"ok": False, "error": f"repo path does not exist: {repo_root}"}

    sys.path.insert(0, str(repo_root))
    status: dict[str, Any] = {"ok": True, "path": str(repo_root), "modules": {}}
    try:
        for name in REPO_IMPORTS:
            try:
                importlib.import_module(name)
            except Exception as exc:  # pragma: no cover - environment-specific import failures
                status["modules"][name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            else:
                status["modules"][name] = {"ok": True}
    finally:
        try:
            sys.path.remove(str(repo_root))
        except ValueError:
            pass
    status["ok"] = all(item.get("ok", False) for item in status["modules"].values())
    return status


def build_report(repo_root: Path | None, timeout: int, skip_helpers: bool, skip_repo_imports: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "skill_root": str(SKILL_ROOT),
        "python": sys.version.split()[0],
        "required_imports": {},
        "optional_imports": {},
        "torch": {"ok": False, "cuda_available": False, "cuda_device_count": 0, "distributed_available": False, "mps_available": False},
        "repo_imports": {"skipped": True},
        "helper_scripts": {},
    }

    for import_name, dist_name in REQUIRED_IMPORTS:
        report["required_imports"][import_name] = _module_status(import_name, dist_name)

    for import_name, dist_name in OPTIONAL_IMPORTS:
        try:
            report["optional_imports"][import_name] = _module_status(import_name, dist_name)
        except Exception as exc:  # pragma: no cover - optional imports can fail in arbitrary ways
            report["optional_imports"][import_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    torch_status = report["required_imports"].get("torch", {})
    if isinstance(torch_status, dict) and torch_status.get("ok"):
        report["torch"] = {
            "ok": True,
            "cuda_available": bool(torch_status.get("cuda_available")),
            "cuda_device_count": int(torch_status.get("cuda_device_count", 0)),
            "torch_cuda_version": torch_status.get("torch_cuda_version"),
            "distributed_available": bool(torch_status.get("distributed_available")),
            "mps_available": bool(torch_status.get("mps_available")),
        }

    if repo_root is not None and not skip_repo_imports:
        report["repo_imports"] = _repo_import_status(repo_root)

    if not skip_helpers:
        report["helper_scripts"] = {relpath: _script_help_status(relpath, timeout) for relpath in HELPER_SCRIPTS}

    return report


def _report_has_failures(report: dict[str, Any], require_cuda: bool) -> bool:
    required_failures = any(not status.get("ok", False) for status in report["required_imports"].values())
    helper_failures = any(not status.get("ok", False) for status in report.get("helper_scripts", {}).values())
    repo_failures = bool(report.get("repo_imports", {}).get("ok") is False and not report.get("repo_imports", {}).get("skipped", False))
    cuda_failure = require_cuda and not bool(report.get("torch", {}).get("cuda_available"))
    return required_failures or helper_failures or repo_failures or cuda_failure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Optional Pyramid-Flow checkout root to import from")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for bundled helper --help checks")
    parser.add_argument("--skip-helpers", action="store_true", help="Skip bundled helper --help checks")
    parser.add_argument("--skip-repo-imports", action="store_true", help="Skip repo module import checks even when --repo is set")
    parser.add_argument("--require-cuda", action="store_true", help="Return a failure if torch cannot see CUDA")
    args = parser.parse_args(argv)

    report = build_report(args.repo, args.timeout, args.skip_helpers, args.skip_repo_imports)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Python: {report['python']}")
        for name, status in report["required_imports"].items():
            if status.get("ok"):
                print(f"{name}: ok {status.get('version') or ''}".rstrip())
            else:
                print(f"{name}: missing/error - {status.get('error')}")
        for name, status in report["optional_imports"].items():
            if status.get("ok"):
                print(f"optional {name}: ok {status.get('version') or ''}".rstrip())
            else:
                print(f"optional {name}: missing/error - {status.get('error')}")
        print(f"torch backend: {report['torch']}")
        print(f"repo imports: {report['repo_imports']}")
        if report.get("helper_scripts"):
            print(f"helper scripts: {report['helper_scripts']}")

    if _report_has_failures(report, args.require_cuda):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

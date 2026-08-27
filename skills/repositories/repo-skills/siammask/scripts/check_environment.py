#!/usr/bin/env python3
"""Read-only SiamMask environment and checkout probe.

This helper is bundled with the generated SiamMask repo skill. It verifies that
an arbitrary SiamMask checkout is importable from the current Python process,
that the Cython region extensions are visible when requested, and that CUDA is
available when the selected workflow requires it. It does not download data,
load checkpoints, run training, or execute benchmark examples.

Example:
  python scripts/check_environment.py --repo-root /path/to/SiamMask --expect-cuda auto --check-cli
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

CORE_IMPORTS = [
    "torch",
    "cv2",
    "numpy",
    "numba",
    "scipy",
    "h5py",
    "PIL.Image",
    "tqdm",
    "colorama",
    "fire",
    "tensorboardX",
    "pycocotools",
    "utils.config_helper",
    "utils.load_helper",
    "utils.benchmark_helper",
    "utils.tracker_config",
    "datasets.siam_mask_dataset",
    "datasets.siam_rpn_dataset",
    "models.siammask",
    "models.siammask_sharp",
    "models.siamrpn",
    "tools.test",
    "tools.train_siammask",
    "tools.train_siammask_refine",
    "tools.train_siamrpn",
    "tools.eval",
]

COMPILED_IMPORTS = [
    "utils.pyvotkit.region",
    "utils.pysot.utils.region",
]

CLI_HELP_SCRIPTS = [
    "tools/test.py",
    "tools/train_siammask.py",
    "tools/train_siammask_refine.py",
    "tools/train_siamrpn.py",
    "tools/eval.py",
    "tools/demo.py",
    "tools/tune_vot.py",
    "tools/tune_vos.py",
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Probe a SiamMask checkout and Python runtime without running native examples.")
    p.add_argument("--repo-root", default=".", help="Path to the SiamMask checkout to inspect. Defaults to the current directory.")
    p.add_argument("--expect-cuda", choices=["auto", "yes", "no"], default="auto", help="Require CUDA to be available (yes), ignore CUDA (no), or report it without requiring it (auto).")
    p.add_argument("--skip-compiled", action="store_true", help="Do not import pyvotkit/pysot Cython region extensions.")
    p.add_argument("--check-cli", action="store_true", help="Run --help checks for the main SiamMask Python entry points.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    return p


def add_repo_to_path(repo_root: Path) -> None:
    sys.path.insert(0, str(repo_root))


def import_many(names: Iterable[str]) -> tuple[list[str], dict[str, str]]:
    ok: list[str] = []
    failures: dict[str, str] = {}
    for name in names:
        try:
            importlib.import_module(name)
            ok.append(name)
        except Exception as exc:  # report, do not hide the failing import
            failures[name] = f"{type(exc).__name__}: {exc}"
    return ok, failures


def cuda_probe(expect: str) -> dict[str, object]:
    try:
        import torch
    except Exception as exc:
        return {"available": False, "required": expect == "yes", "error": f"torch import failed: {exc}"}

    info: dict[str, object] = {
        "available": bool(torch.cuda.is_available()),
        "required": expect == "yes",
        "device_count": int(torch.cuda.device_count()),
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_runtime": getattr(torch.version, "cuda", None),
    }
    if torch.cuda.is_available():
        try:
            info["device_0"] = torch.cuda.get_device_name(0)
            info["smoke_value"] = float((torch.tensor([1.0], device="cuda") * 2).item())
        except Exception as exc:
            info["smoke_error"] = f"{type(exc).__name__}: {exc}"
    return info


def cli_help_probe(repo_root: Path) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result: dict[str, object] = {"checked": [], "failures": {}}
    for rel in CLI_HELP_SCRIPTS:
        script = repo_root / rel
        if not script.exists():
            result["failures"][rel] = "missing script"
            continue
        proc = subprocess.run([sys.executable, str(script), "--help"], cwd=str(repo_root), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            result["checked"].append(rel)
        else:
            result["failures"][rel] = proc.stderr.strip().splitlines()[-1:] or [f"exit {proc.returncode}"]
    return result


def main() -> int:
    args = parser().parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    summary: dict[str, object] = {
        "repo_root": str(repo_root),
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "checks": {},
        "warnings": [],
    }

    if not repo_root.exists():
        summary["checks"]["repo_root"] = "missing"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 2
    if not (repo_root / "README.md").exists() or not (repo_root / "tools" / "test.py").exists():
        summary["warnings"].append("The repo root does not look like a SiamMask checkout: README.md or tools/test.py is missing.")

    add_repo_to_path(repo_root)
    imports = list(CORE_IMPORTS)
    if not args.skip_compiled:
        imports += COMPILED_IMPORTS
    ok, failures = import_many(imports)
    summary["checks"]["imports"] = {"ok_count": len(ok), "failures": failures}
    summary["checks"]["cuda"] = cuda_probe(args.expect_cuda)
    if args.check_cli:
        summary["checks"]["cli_help"] = cli_help_probe(repo_root)

    failed = bool(failures)
    cuda_info = summary["checks"]["cuda"]
    if isinstance(cuda_info, dict) and args.expect_cuda == "yes" and not cuda_info.get("available"):
        failed = True
    if args.check_cli:
        cli = summary["checks"].get("cli_help", {})
        failed = failed or bool(isinstance(cli, dict) and cli.get("failures"))

    summary["status"] = "failed" if failed else "ok"
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

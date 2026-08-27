#!/usr/bin/env python3
"""Read-only diagnostic for legacy MDT CUDA-extension prerequisites."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def command_text(command: list[str]) -> str | None:
    try:
        return subprocess.run(command, check=False, capture_output=True, text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, help="optional checkout to inspect by filename only")
    p.add_argument("--framework-cuda-smoke", action="store_true", help="allocate one tiny torch tensor if torch is installed")
    args = p.parse_args()
    report: dict[str, object] = {"nvcc": shutil.which("nvcc"), "nvidia_smi": shutil.which("nvidia-smi"), "torch": {}}
    try:
        import torch
        report["torch"] = {"version": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": bool(torch.cuda.is_available()), "device_count": int(torch.cuda.device_count())}
        try:
            import torch.utils.ffi  # type: ignore[attr-defined]
            report["torch"]["legacy_ffi"] = True
        except Exception as exc:
            report["torch"]["legacy_ffi"] = False
            report["torch"]["legacy_ffi_error"] = type(exc).__name__
        if args.framework_cuda_smoke and torch.cuda.is_available():
            x = torch.ones((1,), device="cuda")
            report["torch"]["framework_cuda_smoke"] = float(x.sum().cpu()) == 1.0
    except Exception as exc:
        report["torch"] = {"import_error": f"{type(exc).__name__}: {exc}"}
    if report["nvidia_smi"]:
        report["nvidia_smi_query"] = command_text(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    if args.repo_root:
        root = args.repo_root.resolve()
        names = []
        for relative in ("cuda_functions", "models", "README.md"):
            if (root / relative).exists():
                names.append(relative)
        report["repo_evidence_names"] = names
        report["repo_root_exists"] = root.is_dir()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check InternLM-XComposer workflow prerequisites without running models.

The script is stdlib-only by default. It can inspect module availability and run
an optional host CUDA probe through nvidia-smi. It does not download models,
start services, or allocate GPU memory.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import shutil
import subprocess
import sys
from typing import Dict, List


def split_modules(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]


def module_report(name: str) -> Dict[str, object]:
    spec = importlib.util.find_spec(name)
    report: Dict[str, object] = {"name": name, "available": spec is not None}
    if spec is None:
        return report
    report["origin"] = "available"
    # Distribution names often differ from import names; try common spellings.
    candidates = [name, name.replace("_", "-"), name.split(".")[0], name.split(".")[0].replace("_", "-")]
    for candidate in dict.fromkeys(candidates):
        try:
            report["version"] = importlib.metadata.version(candidate)
            report["distribution"] = candidate
            break
        except importlib.metadata.PackageNotFoundError:
            continue
    return report


def cuda_host_report() -> Dict[str, object]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return {"available": False, "error": "nvidia-smi not found"}
    cmd = [
        exe,
        "--query-gpu=name,memory.total,driver_version,compute_cap",
        "--format=csv,noheader,nounits",
    ]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    if proc.returncode != 0:
        return {"available": False, "command": " ".join(cmd), "stderr": proc.stderr.strip()}
    gpus = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 4:
            gpus.append({"name": parts[0], "memory_total_mb": parts[1], "driver_version": parts[2], "compute_capability": parts[3]})
        elif line.strip():
            gpus.append({"raw": line.strip()})
    return {"available": bool(gpus), "count": len(gpus), "gpus": gpus}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check safe InternLM-XComposer environment prerequisites.")
    parser.add_argument("--modules", default="", help="Comma-separated import module names to check with importlib.util.find_spec.")
    parser.add_argument("--check-cuda-host", action="store_true", help="Probe nvidia-smi for visible NVIDIA GPUs without importing torch.")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modules = split_modules(args.modules)
    report = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "modules": [module_report(name) for name in modules],
        "cuda_host": cuda_host_report() if args.check_cuda_host else None,
    }
    missing = [item["name"] for item in report["modules"] if not item.get("available")]
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for item in report["modules"]:
            status = "OK" if item.get("available") else "MISSING"
            version = f" {item.get('version')}" if item.get("version") else ""
            print(f"{status}: {item['name']}{version}")
        if args.check_cuda_host:
            print(json.dumps(report["cuda_host"], indent=2, sort_keys=True))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe top-level DeepKE installation diagnostic.

This root checker imports representative DeepKE packages and common runtime
dependencies. It does not train, download models, call APIs, or mutate configs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from importlib import metadata
from typing import Any, Dict, Sequence, Tuple

IMPORTS: Sequence[Tuple[str, str | None, str]] = (
    ("deepke", "deepke", "core package"),
    ("deepke.name_entity_re.standard", "deepke", "standard NER"),
    ("deepke.relation_extraction.standard", "deepke", "standard RE"),
    ("deepke.attribution_extraction.standard", "deepke", "standard AE"),
    ("deepke.event_extraction.standard", "deepke", "standard EE"),
    ("deepke.triple_extraction.PRGC", "deepke", "PRGC triples"),
    ("deepke.triple_extraction.PURE", "deepke", "PURE triples"),
    ("deepke.triple_extraction.ASP", "deepke", "ASP triples"),
    ("deepke.transform_data", "deepke", "data conversion helpers"),
    ("torch", "torch", "PyTorch"),
    ("transformers", "transformers", "Transformers"),
    ("datasets", "datasets", "HF datasets"),
    ("hydra", "hydra-core", "Hydra configs"),
)


def import_record(module: str, dist: str | None, role: str) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"module": module, "role": role, "distribution": dist, "ok": False, "version": None, "error": None}
    try:
        importlib.import_module(module)
        rec["ok"] = True
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"{type(exc).__name__}: {exc}"
    if dist:
        try:
            rec["version"] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            if rec["ok"]:
                rec["version"] = "imported; distribution metadata not found"
        except Exception as exc:  # noqa: BLE001
            rec["version_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def cuda_info() -> Dict[str, Any]:
    try:
        import torch  # type: ignore

        return {
            "torch_imported": True,
            "torch_version": getattr(torch, "__version__", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"torch_imported": False, "torch_version": None, "available": False, "device_count": 0, "error": f"{type(exc).__name__}: {exc}"}


def build_report() -> Dict[str, Any]:
    return {
        "script": "check_deepke_core.py",
        "python": {"version": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform()},
        "imports": [import_record(module, dist, role) for module, dist, role in IMPORTS],
        "cuda": cuda_info(),
        "notes": [
            "This diagnostic checks imports only; it does not prove model checkpoints, datasets, API credentials, or GPU-heavy workflows are available.",
            "Use the focused sub-skill checkers for supervised, triple, LLM, or MCP workflows before long runs.",
        ],
    }


def has_failures(report: Dict[str, Any], *, require_cuda: bool) -> bool:
    required_modules = {"deepke", "torch", "transformers", "hydra"}
    failures = [not item.get("ok") for item in report["imports"] if item.get("module") in required_modules]
    if require_cuda and not report["cuda"].get("available"):
        failures.append(True)
    return any(failures)


def print_text(report: Dict[str, Any]) -> None:
    print("DeepKE core diagnostic")
    print(f"Python: {report['python']['version']} ({report['python']['platform']})")
    print(f"Executable: {report['python']['executable']}")
    print("\nImports:")
    for item in report["imports"]:
        status = "OK" if item["ok"] else "MISSING"
        version = f" version={item['version']}" if item.get("version") else ""
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']} ({item['role']}){version}{error}")
    cuda = report["cuda"]
    print("\nCUDA:")
    print(f"  torch_imported={cuda.get('torch_imported')} available={cuda.get('available')} device_count={cuda.get('device_count')} torch_version={cuda.get('torch_version')}")
    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely check representative DeepKE imports without running models.")
    parser.add_argument("--require-cuda", action="store_true", help="exit nonzero with --strict if CUDA is unavailable")
    parser.add_argument("--strict", action="store_true", help="exit nonzero when required imports or required CUDA are unavailable")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and has_failures(report, require_cuda=args.require_cuda) else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Probe Hummingbird advanced backend availability without installing packages.

The script is intentionally read-only: it imports packages that are already
available, reports Hummingbird backend aliases, checks PyTorch CUDA visibility,
and optionally allocates one tiny CUDA tensor when --cuda-smoke is requested.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from typing import Any, Dict


def _version(distribution: str, module: Any = None) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except Exception:
        return getattr(module, "__version__", None) if module is not None else None


def _err(exc: BaseException) -> Dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def probe_hummingbird() -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "import_ok": False,
        "version": None,
        "backend_aliases": [],
        "canonical_by_alias": {},
        "canonical_backends": [],
        "error": None,
    }
    try:
        import hummingbird  # noqa: F401
        import hummingbird.ml  # noqa: F401
        import hummingbird.ml.supported as hb_supported

        aliases = {
            str(alias): str(canonical)
            for alias, canonical in hb_supported.backends.items()
            if canonical is not None
        }
        result.update(
            {
                "import_ok": True,
                "version": _version("hummingbird-ml", hummingbird),
                "backend_aliases": sorted(aliases.keys()),
                "canonical_by_alias": dict(sorted(aliases.items())),
                "canonical_backends": sorted(set(aliases.values())),
            }
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["error"] = _err(exc)
    return result


def probe_torch(cuda_smoke: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "import_ok": False,
        "version": None,
        "cuda_compiled_version": None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_names": [],
        "cuda_smoke": {"requested": cuda_smoke, "ok": None, "error": None},
        "error": None,
    }
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        device_count = int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0
        names = []
        if cuda_available and device_count:
            for idx in range(device_count):
                try:
                    names.append(torch.cuda.get_device_name(idx))
                except Exception as exc:  # pragma: no cover - hardware diagnostic path
                    names.append(f"<device {idx} name unavailable: {type(exc).__name__}>")

        result.update(
            {
                "import_ok": True,
                "version": getattr(torch, "__version__", None),
                "cuda_compiled_version": getattr(torch.version, "cuda", None),
                "cuda_available": cuda_available,
                "cuda_device_count": device_count,
                "cuda_device_names": names,
            }
        )

        if cuda_smoke:
            if not cuda_available or device_count < 1:
                result["cuda_smoke"] = {
                    "requested": True,
                    "ok": False,
                    "error": "CUDA is not available to this PyTorch runtime.",
                }
            else:
                try:
                    value = float((torch.ones(1, device="cuda") + 1).cpu().item())
                    result["cuda_smoke"] = {"requested": True, "ok": value == 2.0, "value": value, "error": None}
                except Exception as exc:  # pragma: no cover - hardware diagnostic path
                    result["cuda_smoke"] = {"requested": True, "ok": False, "error": _err(exc)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["error"] = _err(exc)
        if cuda_smoke:
            result["cuda_smoke"] = {"requested": True, "ok": False, "error": _err(exc)}
    return result


def probe_tvm() -> Dict[str, Any]:
    result: Dict[str, Any] = {"importable": False, "version": None, "error": None}
    spec = importlib.util.find_spec("tvm")
    if spec is None:
        return result
    try:
        tvm = importlib.import_module("tvm")
        result.update({"importable": True, "version": getattr(tvm, "__version__", None)})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["error"] = _err(exc)
    return result


def build_report(cuda_smoke: bool) -> Dict[str, Any]:
    report = {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "hummingbird": probe_hummingbird(),
        "torch": probe_torch(cuda_smoke),
        "tvm": probe_tvm(),
    }
    cuda_smoke_status = report["torch"].get("cuda_smoke", {})
    report["ok"] = bool(report["hummingbird"]["import_ok"]) and (
        not cuda_smoke or bool(cuda_smoke_status.get("ok"))
    )
    return report


def print_human(report: Dict[str, Any]) -> None:
    hb = report["hummingbird"]
    torch = report["torch"]
    tvm = report["tvm"]
    print(f"Python: {report['python']['version']} ({report['python']['implementation']})")
    print(f"Hummingbird import: {'ok' if hb['import_ok'] else 'failed'}")
    if hb["version"]:
        print(f"Hummingbird version: {hb['version']}")
    if hb["backend_aliases"]:
        print("Backend aliases: " + ", ".join(hb["backend_aliases"]))
    if hb["error"]:
        print(f"Hummingbird error: {hb['error']}")
    print(f"Torch import: {'ok' if torch['import_ok'] else 'failed'}")
    if torch["version"]:
        print(f"Torch version: {torch['version']}")
    print(f"Torch CUDA compiled version: {torch['cuda_compiled_version']}")
    print(f"Torch CUDA available: {torch['cuda_available']}")
    print(f"Torch CUDA device count: {torch['cuda_device_count']}")
    if torch["cuda_device_names"]:
        print("Torch CUDA devices: " + ", ".join(torch["cuda_device_names"]))
    if torch["error"]:
        print(f"Torch error: {torch['error']}")
    smoke = torch.get("cuda_smoke", {})
    if smoke.get("requested"):
        print(f"CUDA smoke: {'ok' if smoke.get('ok') else 'failed'}")
        if smoke.get("error"):
            print(f"CUDA smoke error: {smoke['error']}")
    else:
        print("CUDA smoke: skipped")
    print(f"TVM importable: {tvm['importable']}")
    if tvm["version"]:
        print(f"TVM version: {tvm['version']}")
    if tvm["error"]:
        print(f"TVM error: {tvm['error']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Hummingbird backend, CUDA, and TVM availability.")
    parser.add_argument("--json", action="store_true", help="Print the probe report as JSON.")
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="Allocate one tiny CUDA tensor if CUDA is visible. No CUDA allocation is attempted without this flag.",
    )
    args = parser.parse_args(argv)

    report = build_report(cuda_smoke=args.cuda_smoke)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

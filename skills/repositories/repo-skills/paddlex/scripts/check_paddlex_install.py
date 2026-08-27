#!/usr/bin/env python3
"""Read-only PaddleX installation health check.

Run inside the Python environment intended for PaddleX work. The script does
not import or depend on a source checkout and does not install anything.
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
import json
import shutil
from typing import Any, Dict


DISTS = [
    "paddlex",
    "paddlepaddle",
    "paddlepaddle-gpu",
    "opencv-contrib-python",
    "faiss-cpu",
    "soundfile",
    "paddle2onnx",
    "fastapi",
    "vllm",
    "sglang",
]

MODULES = ["paddlex", "paddle", "cv2", "faiss", "soundfile", "paddle2onnx"]


def _dist_version(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def _module_probe(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report probe failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": str(getattr(mod, "__version__", "unknown"))}


def _paddle_cuda() -> Dict[str, Any]:
    try:
        import paddle
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    out: Dict[str, Any] = {
        "available": True,
        "version": getattr(paddle, "__version__", None),
    }
    try:
        out["compiled_with_cuda"] = bool(paddle.is_compiled_with_cuda())
    except Exception as exc:  # noqa: BLE001
        out["compiled_with_cuda_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _entry_points() -> Dict[str, str]:
    eps: Dict[str, str] = {}
    for ep in md.entry_points(group="console_scripts"):
        if ep.name.startswith("paddlex"):
            eps[ep.name] = ep.value
    return dict(sorted(eps.items()))


def main() -> int:
    report = {
        "distributions": {name: _dist_version(name) for name in DISTS},
        "modules": {name: _module_probe(name) for name in MODULES},
        "paddle_backend": _paddle_cuda(),
        "executables": {
            "paddlex": shutil.which("paddlex"),
            "paddlex_genai_server": shutil.which("paddlex_genai_server"),
        },
        "entry_points": _entry_points(),
        "notes": [
            "CPU import success is not proof of GPU/HPI readiness.",
            "Install deployment plugins only for the selected workflow.",
            "Use sub-skills/pipelines for create_pipeline workflows, sub-skills/modules for training/export, and sub-skills/deployment for HPI/serving/Paddle2ONNX/GenAI.",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    paddlex_ok = report["modules"]["paddlex"]["ok"]
    paddle_ok = report["modules"]["paddle"]["ok"]
    return 0 if paddlex_ok and paddle_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

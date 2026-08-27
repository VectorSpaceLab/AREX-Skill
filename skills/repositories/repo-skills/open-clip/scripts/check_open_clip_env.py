#!/usr/bin/env python3
"""Check an OpenCLIP installation without downloading model weights.

The script reports importability, package metadata, model/pretrained registry
counts, optional audio/training module availability, and selected torch backend
facts. It does not instantiate pretrained weights or access datasets.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any


def _import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "module": name, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # pragma: no cover - environment-specific
        return {"ok": False, "module": name, "error": repr(exc)}


def _metadata(dist_name: str) -> dict[str, Any]:
    try:
        return {"ok": True, "name": dist_name, "version": importlib.metadata.version(dist_name)}
    except Exception as exc:  # pragma: no cover - environment-specific
        return {"ok": False, "name": dist_name, "error": repr(exc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-torch", action="store_true", help="Include torch version/backend availability facts.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    report: dict[str, Any] = {
        "distribution": _metadata("open_clip_torch"),
        "imports": {
            "open_clip": _import_status("open_clip"),
            "open_clip_train": _import_status("open_clip_train"),
            "open_clip.audio": _import_status("open_clip.audio"),
        },
    }

    if report["imports"]["open_clip"]["ok"]:
        import open_clip

        report["open_clip"] = {
            "version": getattr(open_clip, "__version__", None),
            "model_count": len(open_clip.list_models()),
            "models_preview": open_clip.list_models()[:20],
            "pretrained_count": len(open_clip.list_pretrained()),
            "pretrained_preview": open_clip.list_pretrained(as_str=True)[:20],
            "audio_available": getattr(open_clip, "AUDIO_AVAILABLE", None),
        }

    if args.show_torch:
        torch_status = _import_status("torch")
        report["torch"] = torch_status
        if torch_status["ok"]:
            import torch

            backend = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
            if torch.cuda.is_available():
                backend["cuda_device_0"] = torch.cuda.get_device_name(0)
                backend["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
            report["torch_backend"] = backend

    ok = report["distribution"]["ok"] and report["imports"]["open_clip"]["ok"]
    report["ok"] = bool(ok)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OpenCLIP environment report")
        print(f"ok: {report['ok']}")
        print(f"distribution: {report['distribution']}")
        for name, status in report["imports"].items():
            print(f"{name}: {status}")
        if "open_clip" in report:
            facts = report["open_clip"]
            print(f"version: {facts['version']}")
            print(f"model_count: {facts['model_count']}")
            print(f"pretrained_count: {facts['pretrained_count']}")
            print(f"audio_available: {facts['audio_available']}")
        if "torch_backend" in report:
            print(f"torch_backend: {report['torch_backend']}")

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

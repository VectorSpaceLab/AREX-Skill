#!/usr/bin/env python3
"""Safe Otter environment probe.

Checks imports and dependency versions without downloading models, opening
network connections, starting services, or loading checkpoints.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict:
    try:
        importlib.import_module(module)
        return {"module": module, "ok": True}
    except Exception as exc:  # noqa: BLE001 - probe should report import errors
        return {"module": module, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Otter package imports and dependency versions safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--check-cuda", action="store_true", help="Also run a tiny torch CUDA availability/allocation check.")
    args = parser.parse_args()

    dists = [
        "otter-ai",
        "torch",
        "transformers",
        "tokenizers",
        "huggingface_hub",
        "accelerate",
        "peft",
        "open_clip_torch",
        "gradio",
        "fastapi",
        "deepspeed",
        "litellm",
        "xformers",
    ]
    modules = [
        "otter_ai",
        "otter_ai.models.otter.configuration_otter",
        "otter_ai.models.otter.modeling_otter",
        "otter_ai.models.flamingo.configuration_flamingo",
    ]
    report = {
        "schema": "otter.environment-check.v1",
        "python": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in dists},
        "imports": [import_status(module) for module in modules],
        "cuda": {"checked": False},
        "warnings": [],
    }

    if report["distributions"].get("transformers") == "4.35.1":
        hub = report["distributions"].get("huggingface_hub")
        accel = report["distributions"].get("accelerate")
        peft = report["distributions"].get("peft")
        if hub and hub != "0.17.3":
            report["warnings"].append("Repository-pinned transformers==4.35.1 was inspected with huggingface_hub==0.17.3; verify imports after changing Hub versions.")
        if accel and accel not in {"0.23.0", "0.24.0", "0.25.0"}:
            report["warnings"].append("Newer accelerate versions may require Hugging Face Hub APIs unavailable with tokenizers==0.14.1 constraints.")
        if peft and peft != "0.4.0":
            report["warnings"].append("PEFT 0.4.0 matched the repository-era stack during inspection; newer PEFT may require newer Hugging Face Hub modules.")

    if args.check_cuda:
        report["cuda"] = {"checked": True, "available": False}
        torch_status = import_status("torch")
        if not torch_status["ok"]:
            report["cuda"].update({"ok": False, "error": torch_status.get("error")})
        else:
            import torch

            available = bool(torch.cuda.is_available())
            report["cuda"].update({
                "ok": available,
                "available": available,
                "device_count": int(torch.cuda.device_count()) if available else 0,
                "torch_cuda": getattr(torch.version, "cuda", None),
            })
            if available:
                try:
                    torch.empty((1,), device="cuda")
                    report["cuda"]["allocation"] = "passed"
                except Exception as exc:  # noqa: BLE001
                    report["cuda"].update({"ok": False, "allocation": "failed", "error": str(exc)})

    ok = all(item["ok"] for item in report["imports"])
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Python: {report['python']}")
        for name, version in report["distributions"].items():
            print(f"{name}: {version or 'not installed'}")
        for item in report["imports"]:
            print(f"import {item['module']}: {'ok' if item['ok'] else 'ERROR ' + item['error_type'] + ': ' + item['error']}")
        if report["cuda"].get("checked"):
            print(f"cuda: {report['cuda']}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

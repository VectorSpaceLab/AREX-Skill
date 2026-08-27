#!/usr/bin/env python3
"""Read-only PaddleX deployment capability probe.

The script checks imports/entry points and prints plugin command reminders. It
does not install packages, start servers, convert models, or mutate files.
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
import json
import shutil
from typing import Dict, List


MODULES = {
    "paddlex": "paddlex",
    "paddle": "paddle",
    "paddle2onnx": "paddle2onnx",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "openai": "openai",
    "vllm": "vllm",
    "sglang": "sglang",
    "torch": "torch",
    "transformers": "transformers",
}

PLUGIN_COMMANDS = [
    "paddlex --install serving",
    "paddlex --install paddle2onnx",
    "paddlex --install hpi-cpu",
    "paddlex --install hpi-gpu",
    "paddlex --install genai-client",
    "paddlex --install genai-vllm-server",
    "paddlex --install genai-sglang-server",
]


def _module_status(module: str) -> Dict[str, str]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - report import probe failures.
        return {"available": "false", "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(imported, "__version__", None)
    return {"available": "true", "version": str(version) if version is not None else "unknown"}


def _entry_points() -> List[str]:
    out: List[str] = []
    for ep in md.entry_points(group="console_scripts"):
        if ep.name.startswith("paddlex"):
            out.append(f"{ep.name} -> {ep.value}")
    return sorted(out)


def main() -> int:
    status = {
        "executables": {
            "paddlex": shutil.which("paddlex"),
            "paddlex_genai_server": shutil.which("paddlex_genai_server"),
        },
        "entry_points": _entry_points(),
        "modules": {label: _module_status(module) for label, module in MODULES.items()},
        "plugin_install_commands": PLUGIN_COMMANDS,
        "notes": [
            "This is a read-only probe; install only the plugin needed by the chosen deployment workflow.",
            "GPU/HPI readiness requires a GPU-enabled PaddlePaddle and matching backend plugin; physical GPU visibility alone is insufficient.",
            "Paddle2ONNX expects an exported Paddle inference model directory.",
            "GenAI client workflows usually need server_url or equivalent backend config.",
        ],
    }
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

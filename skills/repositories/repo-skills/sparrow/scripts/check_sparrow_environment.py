#!/usr/bin/env python3
"""Offline Sparrow environment checker.

This helper verifies package/import and optional backend/service signals without
starting Sparrow services or running model inference. It is safe to run before
expensive OCR/VLM/agent/UI checks.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import socket
import sys
from importlib import metadata
from typing import Any


MODULES = {
    "sparrow_parse": "Sparrow Parse package",
    "fastapi": "FastAPI service framework",
    "typer": "Sparrow LLM engine CLI framework",
    "pdf2image": "PDF-to-image helper",
    "pypdf": "PDF page counting",
    "PIL": "Pillow image processing",
    "jsonschema": "JSON schema validation",
    "bs4": "HTML table template parsing",
}

OPTIONAL_MODULES = {
    "torch": "Torch / CUDA-capable package dependency",
    "torchvision": "Table detection transforms",
    "vllm": "vLLM backend",
    "mlx_vlm": "MLX VLM backend",
    "ollama": "Ollama client",
    "mistralai": "Mistral API client",
    "paddleocr": "PaddleOCR runtime",
    "prefect": "Sparrow Agents flow runtime",
    "celery": "Sparrow Agents async task runtime",
    "oracledb": "Dashboard/API logging database runtime",
}

DISTRIBUTIONS = ["sparrow-parse"]


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", None)
        return {"module": module, "ok": True, "version": version}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def dist_status(name: str) -> dict[str, Any]:
    try:
        return {"distribution": name, "ok": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"distribution": name, "ok": False, "error": "not installed"}


def tcp_probe(host: str, port: int, timeout: float) -> dict[str, Any]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return {"host": host, "port": port, "ok": True}
        except OSError as exc:
            return {"host": host, "port": port, "ok": False, "error": str(exc)}


def collect(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": [dist_status(d) for d in DISTRIBUTIONS],
        "requiredModules": {desc: import_status(module) for module, desc in MODULES.items()},
        "optionalModules": {desc: import_status(module) for module, desc in OPTIONAL_MODULES.items()},
        "systemTools": {
            "pdftoppm": {"ok": shutil.which("pdftoppm") is not None, "pathKnown": shutil.which("pdftoppm") is not None},
            "ollama": {"ok": shutil.which("ollama") is not None, "pathKnown": shutil.which("ollama") is not None},
            "node": {"ok": shutil.which("node") is not None, "pathKnown": shutil.which("node") is not None},
            "npm": {"ok": shutil.which("npm") is not None, "pathKnown": shutil.which("npm") is not None},
            "redis-server": {"ok": shutil.which("redis-server") is not None, "pathKnown": shutil.which("redis-server") is not None},
        },
        "warnings": [],
    }

    torch_info = result["optionalModules"]["Torch / CUDA-capable package dependency"]
    if torch_info["ok"]:
        try:
            import torch  # type: ignore

            result["torch"] = {
                "version": getattr(torch, "__version__", None),
                "cudaVersion": getattr(torch.version, "cuda", None),
                "cudaAvailable": bool(torch.cuda.is_available()),
                "cudaDeviceCount": int(torch.cuda.device_count()),
            }
        except Exception as exc:  # pragma: no cover
            result["torch"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if args.check_http:
        result["tcp"] = {
            "llmApi": tcp_probe(args.host, args.llm_port, args.timeout),
            "ocrApi": tcp_probe(args.host, args.ocr_port, args.timeout),
            "agentsApi": tcp_probe(args.host, args.agents_port, args.timeout),
            "ollama": tcp_probe(args.host, args.ollama_port, args.timeout),
            "redis": tcp_probe(args.host, args.redis_port, args.timeout),
        }
    else:
        result["warnings"].append("HTTP/TCP service probes skipped; pass --check-http to test local ports without sending requests.")

    if any(not item["ok"] for item in result["distributions"]):
        result["warnings"].append("sparrow-parse distribution metadata is missing; install Sparrow Parse before package-level extraction.")
    if not result["systemTools"]["pdftoppm"]["ok"]:
        result["warnings"].append("Poppler pdftoppm is not visible; PDF-to-image flows may fail.")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sparrow package/backend/service readiness without running model inference.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--check-http", action="store_true", help="Probe local TCP ports for Sparrow/Ollama/Redis services.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for optional TCP probes.")
    parser.add_argument("--llm-port", type=int, default=8002, help="Sparrow LLM API port.")
    parser.add_argument("--ocr-port", type=int, default=8004, help="Sparrow OCR API port if used.")
    parser.add_argument("--agents-port", type=int, default=8003, help="Sparrow Agents API port.")
    parser.add_argument("--ollama-port", type=int, default=11434, help="Ollama daemon port.")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port for async agents.")
    parser.add_argument("--timeout", type=float, default=0.5, help="TCP probe timeout in seconds.")
    args = parser.parse_args()

    result = collect(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        for dist in result["distributions"]:
            print(f"Distribution {dist['distribution']}: {'OK ' + dist.get('version', '') if dist['ok'] else 'MISSING'}")
        print("\nRequired modules:")
        for desc, status in result["requiredModules"].items():
            print(f"- {desc}: {'OK' if status['ok'] else 'MISSING'}")
        print("\nOptional modules:")
        for desc, status in result["optionalModules"].items():
            print(f"- {desc}: {'OK' if status['ok'] else 'not installed/failed'}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe H2O LLM Studio runtime environment checker.

This script verifies Python/package importability, runtime-root assets, optional
CUDA availability, and basic config-construction assumptions. It does not start
Wave, download models/data, run training, upload artifacts, or mutate user data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any


def status(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    row = {"ok": ok, "message": message}
    row.update(extra)
    return row


def check_imports() -> list[dict[str, Any]]:
    rows = []
    for module in [
        "llm_studio",
        "llm_studio.app",
        "llm_studio.src.utils.config_utils",
        "llm_studio.src.utils.data_utils",
    ]:
        try:
            mod = importlib.import_module(module)
            rows.append(status(True, f"imported {module}", file=getattr(mod, "__file__", None)))
        except Exception as exc:  # pragma: no cover - diagnostic path
            rows.append(status(False, f"failed to import {module}: {type(exc).__name__}: {exc}"))
    return rows


def check_runtime_root(root: Path, check_config_assets: bool) -> list[dict[str, Any]]:
    required = ["llm_studio", "pyproject.toml"]
    if check_config_assets:
        required += ["prompts", "model_cards", "static"]
    rows = []
    for rel in required:
        p = root / rel
        rows.append(status(p.exists(), f"runtime asset {rel}: {'present' if p.exists() else 'missing'}", path=rel))
    return rows


def check_config_smoke(root: Path) -> list[dict[str, Any]]:
    cwd = Path.cwd()
    try:
        os.chdir(root)
        from llm_studio.python_configs.text_causal_language_modeling_config import (
            ConfigProblemBase as CLM,
        )
        from llm_studio.src.utils.config_utils import convert_cfg_base_to_nested_dictionary

        cfg = CLM()
        d = convert_cfg_base_to_nested_dictionary(cfg)
        return [status(d.get("problem_type") == "text_causal_language_modeling", "constructed causal-LM config", problem_type=d.get("problem_type"))]
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [status(False, f"config smoke failed: {type(exc).__name__}: {exc}")]
    finally:
        os.chdir(cwd)


def check_cuda() -> list[dict[str, Any]]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [status(False, f"torch import failed: {type(exc).__name__}: {exc}")]

    rows = [
        status(True, "torch imported", version=getattr(torch, "__version__", None), cuda_version=getattr(torch.version, "cuda", None)),
        status(bool(torch.cuda.is_available()), f"torch CUDA available: {torch.cuda.is_available()}", device_count=torch.cuda.device_count()),
    ]
    if torch.cuda.is_available():
        try:
            device_name = torch.cuda.get_device_name(0)
            capability = torch.cuda.get_device_capability(0)
            torch.empty((1,), device="cuda")
            rows.append(status(True, "tiny CUDA tensor allocation succeeded", device_name=device_name, capability=list(capability)))
        except Exception as exc:  # pragma: no cover - diagnostic path
            rows.append(status(False, f"tiny CUDA allocation failed: {type(exc).__name__}: {exc}"))
    return rows


def check_deepspeed(cuda_home: str | None) -> list[dict[str, Any]]:
    rows = []
    if cuda_home:
        os.environ.setdefault("CUDA_HOME", cuda_home)
    rows.append(status(bool(os.environ.get("CUDA_HOME")), "CUDA_HOME is set" if os.environ.get("CUDA_HOME") else "CUDA_HOME is not set", CUDA_HOME_set=bool(os.environ.get("CUDA_HOME"))))
    if os.environ.get("CUDA_HOME"):
        nvcc = Path(os.environ["CUDA_HOME"]) / "bin" / "nvcc"
        rows.append(status(nvcc.exists(), "nvcc under CUDA_HOME" if nvcc.exists() else "nvcc missing under CUDA_HOME"))
    try:
        import deepspeed

        rows.append(status(True, "deepspeed imported", version=getattr(deepspeed, "__version__", None)))
    except Exception as exc:  # pragma: no cover - diagnostic path
        rows.append(status(False, f"deepspeed import failed: {type(exc).__name__}: {exc}"))
    return rows


def port_open(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port)) == 0
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check H2O LLM Studio runtime prerequisites without side effects.")
    parser.add_argument("--runtime-root", default=".", help="Runtime root containing llm_studio/ and runtime assets; default: current directory.")
    parser.add_argument("--check-config-assets", action="store_true", help="Require prompts/, model_cards/, and static/ under the runtime root.")
    parser.add_argument("--config-smoke", action="store_true", help="Instantiate a minimal config from the runtime root.")
    parser.add_argument("--check-cuda", action="store_true", help="Probe torch CUDA availability with a tiny allocation if available.")
    parser.add_argument("--check-deepspeed", action="store_true", help="Try to import DeepSpeed; useful before trainer commands.")
    parser.add_argument("--cuda-home", default=None, help="Optional CUDA_HOME to set for the DeepSpeed check.")
    parser.add_argument("--port", type=int, default=10101, help="Local Wave port to check for an existing listener; default: 10101.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    root = Path(args.runtime_root).expanduser().resolve()
    checks: list[dict[str, Any]] = []
    checks.append(status(root.exists(), "runtime root exists" if root.exists() else "runtime root is missing", runtime_root=str(root)))
    if root.exists():
        checks.extend(check_runtime_root(root, args.check_config_assets))
    checks.extend(check_imports())
    if args.config_smoke:
        checks.extend(check_config_smoke(root))
    if args.check_cuda:
        checks.extend(check_cuda())
    if args.check_deepspeed:
        checks.extend(check_deepspeed(args.cuda_home))
    checks.append(status(not port_open(args.port), f"port {args.port} is free" if not port_open(args.port) else f"port {args.port} already has a listener"))

    ok = all(row["ok"] for row in checks if not row["message"].startswith("torch CUDA available: False"))
    result = {"ok": ok, "checks": checks}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for row in checks:
            marker = "OK" if row["ok"] else "WARN"
            print(f"[{marker}] {row['message']}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

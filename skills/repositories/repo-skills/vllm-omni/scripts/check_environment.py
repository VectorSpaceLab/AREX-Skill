#!/usr/bin/env python3
"""Safe vLLM-Omni environment checker.

The checker imports package metadata, vLLM, vLLM-Omni, and optionally verifies a
small CUDA allocation. It does not download model weights or start a server.

Examples:
    python scripts/check_environment.py
    python scripts/check_environment.py --require-vllm 0.26 --require-cuda --json
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as md
import io
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CheckResult:
    ok: bool = True
    python: str = sys.version.split()[0]
    distributions: dict[str, str | None] = field(default_factory=dict)
    imports: dict[str, str] = field(default_factory=dict)
    cuda: dict[str, Any] = field(default_factory=dict)
    cli: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)


def dist_version(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def parse_major_minor(version: str | None) -> tuple[int, int] | None:
    if not version:
        return None
    parts = []
    for item in version.replace("+", ".").replace("-", ".").split("."):
        if item.isdigit():
            parts.append(int(item))
            if len(parts) == 2:
                return tuple(parts)  # type: ignore[return-value]
        elif parts:
            break
    return None


def check_import(result: CheckResult, module: str) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            imported = importlib.import_module(module)
        result.imports[module] = getattr(imported, "__file__", "built-in") or "built-in"
    except Exception as exc:
        result.fail(f"failed to import {module}: {type(exc).__name__}: {exc}")
    combined = (stdout.getvalue() + stderr.getvalue()).strip()
    if combined:
        snippet = combined.replace("\n", " | ")[:500]
        result.warnings.append(f"import {module} produced diagnostic output: {snippet}")


def check_cuda(result: CheckResult, require: bool) -> None:
    try:
        import torch
    except Exception as exc:
        if require:
            result.fail(f"CUDA required but torch import failed: {type(exc).__name__}: {exc}")
        else:
            result.warnings.append(f"torch import failed; CUDA not checked: {type(exc).__name__}: {exc}")
        return
    data: dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda": getattr(getattr(torch, "version", None), "cuda", None),
        "available": bool(torch.cuda.is_available()) if hasattr(torch, "cuda") else False,
        "device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if data["available"]:
        data["device0"] = torch.cuda.get_device_name(0)
        data["capability0"] = ".".join(str(x) for x in torch.cuda.get_device_capability(0))
        torch.empty((1,), device="cuda")
        data["tiny_allocation"] = "passed"
    elif require:
        result.fail("CUDA required but torch.cuda.is_available() is false")
    else:
        result.warnings.append("CUDA not available; CPU/parser checks may still work but live model serving is not verified")
    result.cuda = data


def check_cli(result: CheckResult) -> None:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "vllm_omni.entrypoints.cli.main", "serve", "--omni", "--help=OmniConfig"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        result.cli = {"exit_code": proc.returncode, "stdout_head": proc.stdout[:1000], "stderr_head": proc.stderr[:1000]}
        if proc.returncode != 0 or "OmniConfig" not in proc.stdout:
            result.fail("CLI OmniConfig help did not complete successfully")
    except Exception as exc:
        result.fail(f"CLI help check failed: {type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check vLLM-Omni imports, version alignment, CLI help, and optional CUDA.")
    parser.add_argument("--require-vllm", default=None, help="Required upstream vLLM major.minor prefix, e.g. 0.26")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable")
    parser.add_argument("--skip-cli", action="store_true", help="Skip OmniConfig CLI help check")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    result = CheckResult()
    for dist in ["vllm", "vllm-omni", "torch", "transformers", "diffusers"]:
        result.distributions[dist] = dist_version(dist)
        if result.distributions[dist] is None and dist in {"vllm", "vllm-omni"}:
            result.fail(f"distribution {dist!r} is not installed")

    for module in ["vllm", "vllm_omni", "vllm_omni.entrypoints.omni", "vllm_omni.entrypoints.cli.serve"]:
        check_import(result, module)

    if args.require_vllm:
        got = result.distributions.get("vllm")
        if got is None or not got.startswith(args.require_vllm):
            result.fail(f"vllm version {got!r} does not start with required prefix {args.require_vllm!r}")

    vllm_mm = parse_major_minor(result.distributions.get("vllm"))
    omni_mm = parse_major_minor(result.distributions.get("vllm-omni"))
    if vllm_mm and omni_mm and vllm_mm != omni_mm:
        result.warnings.append(f"vllm major/minor {vllm_mm} differs from vllm-omni metadata {omni_mm}")

    check_cuda(result, args.require_cuda)
    if not args.skip_cli:
        check_cli(result)

    payload = asdict(result)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OK" if result.ok else "FAILED")
        print("distributions:")
        for name, version in result.distributions.items():
            print(f"  {name}: {version}")
        print("imports:")
        for name in result.imports:
            print(f"  {name}: ok")
        if result.cuda:
            print("cuda:", result.cuda)
        for warning in result.warnings:
            print("WARNING:", warning)
        for error in result.errors:
            print("ERROR:", error)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

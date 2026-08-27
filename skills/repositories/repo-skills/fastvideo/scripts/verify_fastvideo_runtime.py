#!/usr/bin/env python3
"""Lightweight FastVideo runtime probe.

This helper verifies imports, public API signatures, console help, and optional
CUDA visibility without downloading models or starting long-lived services.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _record(results: list[dict[str, Any]], name: str, status: str, detail: str = "") -> None:
    results.append({"name": name, "status": status, "detail": detail})


def _run_help(command: list[str], timeout: int) -> tuple[bool, str]:
    exe = shutil.which(command[0])
    if exe is None:
        return False, f"{command[0]!r} not found on PATH"
    proc = subprocess.run(
        [exe, *command[1:]],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    first_line = (proc.stdout or "").splitlines()[0] if proc.stdout else ""
    return proc.returncode == 0, first_line or f"exit {proc.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a FastVideo inspection/runtime environment.")
    parser.add_argument("--cuda", action="store_true", help="Require torch CUDA availability and allocate a tiny tensor.")
    parser.add_argument("--dreamverse", action="store_true", help="Also check Dreamverse console scripts/imports.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip console-script --help checks.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for each CLI help command.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines.")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    ok = True

    try:
        fv_version = version("fastvideo")
        _record(results, "distribution:fastvideo", "ok", fv_version)
    except PackageNotFoundError as exc:
        _record(results, "distribution:fastvideo", "fail", str(exc))
        ok = False

    try:
        import fastvideo  # type: ignore
        from fastvideo import PipelineConfig, SamplingParam, VideoGenerator  # type: ignore

        detail = f"version={getattr(fastvideo, '__version__', 'unknown')}"
        _record(results, "import:fastvideo", "ok", detail)
        _record(results, "api:VideoGenerator.from_pretrained", "ok", str(inspect.signature(VideoGenerator.from_pretrained)))
        _record(results, "api:VideoGenerator.generate", "ok", str(inspect.signature(VideoGenerator.generate)))
        _record(results, "api:PipelineConfig.from_pretrained", "ok", str(inspect.signature(PipelineConfig.from_pretrained)))
        _record(results, "api:SamplingParam.from_pretrained", "ok", str(inspect.signature(SamplingParam.from_pretrained)))
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        _record(results, "import/api:fastvideo", "fail", repr(exc))
        ok = False

    try:
        kernel = importlib.import_module("fastvideo_kernel")
        _record(results, "import:fastvideo_kernel", "ok", f"Int8Linear={hasattr(kernel, 'Int8Linear')}")
    except Exception as exc:  # noqa: BLE001 - kernel may be optional on some scopes
        _record(results, "import:fastvideo_kernel", "warn", repr(exc))

    try:
        torch = importlib.import_module("torch")
        detail = f"torch={torch.__version__} cuda={getattr(torch.version, 'cuda', None)} available={torch.cuda.is_available()} count={torch.cuda.device_count()}"
        if args.cuda:
            if not torch.cuda.is_available():
                raise RuntimeError(detail)
            tensor = torch.empty((1,), device="cuda")
            detail += f" device0={torch.cuda.get_device_name(0)} cap={torch.cuda.get_device_capability(0)} tensor={tensor.device}"
        _record(results, "backend:torch", "ok", detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "backend:torch", "fail" if args.cuda else "warn", repr(exc))
        if args.cuda:
            ok = False

    if args.dreamverse:
        for module in ("dreamverse.main", "dreamverse.mock_server"):
            try:
                importlib.import_module(module)
                _record(results, f"import:{module}", "ok", "")
            except Exception as exc:  # noqa: BLE001
                _record(results, f"import:{module}", "fail", repr(exc))
                ok = False

    if not args.skip_cli:
        commands = [
            ["fastvideo", "--help"],
            ["fastvideo", "generate", "--help"],
            ["fastvideo", "serve", "--help"],
            ["fastvideo", "router-serve", "--help"],
        ]
        if args.dreamverse:
            commands.extend([
                ["dreamverse-server", "--help"],
                ["dreamverse-mock-server", "--help"],
            ])
        for command in commands:
            passed, detail = _run_help(command, args.timeout)
            _record(results, "cli:" + " ".join(command), "ok" if passed else "fail", detail)
            ok = ok and passed

    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2, sort_keys=True))
    else:
        for item in results:
            suffix = f" - {item['detail']}" if item.get("detail") else ""
            print(f"[{item['status']}] {item['name']}{suffix}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

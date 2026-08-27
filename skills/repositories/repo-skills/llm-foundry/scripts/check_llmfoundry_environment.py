#!/usr/bin/env python3
"""Safe root environment check for the LLM Foundry repo skill.

The check imports the installed package, verifies the `llmfoundry` console
entry point is discoverable, probes registry CLI help, and reports torch/CUDA
availability. It never downloads models/data, starts training/evaluation, or
uses credentials.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def run_cmd(cmd: list[str], timeout: float = 20.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except Exception as exc:
        return {"cmd": cmd, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "cmd": cmd,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:20],
        "stderr_head": proc.stderr.splitlines()[:20],
    }


def probe_imports() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        out["distribution_version"] = version("llm-foundry")
    except PackageNotFoundError:
        out["distribution_version"] = None
        out["distribution_error"] = "llm-foundry distribution metadata not found"
    try:
        import llmfoundry
        out["import_ok"] = True
        out["module_version"] = getattr(llmfoundry, "__version__", None)
    except Exception as exc:
        out["import_ok"] = False
        out["import_error"] = f"{type(exc).__name__}: {exc}"
        return out
    try:
        from llmfoundry.models.mpt import MPTConfig
        cfg = MPTConfig(d_model=64, n_heads=4, n_layers=1, max_seq_len=16, attn_config={"attn_impl": "torch"})
        out["mpt_config_ok"] = True
        out["mpt_config"] = {"model_type": cfg.model_type, "max_seq_len": cfg.max_seq_len, "attn_impl": cfg.attn_config.get("attn_impl")}
    except Exception as exc:
        out["mpt_config_ok"] = False
        out["mpt_config_error"] = f"{type(exc).__name__}: {exc}"
    return out


def probe_torch() -> dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        return {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    data: dict[str, Any] = {
        "import_ok": True,
        "version": getattr(torch, "__version__", "unknown"),
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }
    if torch.cuda.is_available():
        try:
            data["device_0"] = torch.cuda.get_device_name(0)
            data["capability_0"] = torch.cuda.get_device_capability(0)
        except Exception as exc:
            data["cuda_detail_error"] = f"{type(exc).__name__}: {exc}"
    return data


def collect(check_cli: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "imports": probe_imports(),
        "torch": probe_torch(),
        "cli": {},
        "notes": [],
    }
    if check_cli:
        exe = shutil.which("llmfoundry")
        report["cli"]["executable_found"] = bool(exe)
        if exe:
            report["cli"]["root_help"] = run_cmd([exe, "--help"])
            report["cli"]["registry_models"] = run_cmd([exe, "registry", "get", "--group", "models"])
        else:
            report["notes"].append("llmfoundry console script is not on PATH; try python -m pip install llm-foundry or run through the environment's scripts directory")
    if report["torch"].get("cuda_available"):
        report["notes"].append("torch CUDA is visible, but this check does not verify flash-attn, TransformerEngine, MegaBlocks, FasterTransformer, or distributed training")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely verify installed LLM Foundry import, CLI, registry, and torch backend availability.")
    parser.add_argument("--no-cli", action="store_true", help="Skip llmfoundry console-script checks")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)
    report = collect(check_cli=not args.no_cli)
    ok = bool(report["imports"].get("import_ok"))
    if args.json:
        print(json.dumps({"ok": ok, **report}, indent=2, default=str))
    else:
        print(f"LLM Foundry import: {'ok' if ok else 'failed'}")
        print(f"Distribution version: {report['imports'].get('distribution_version')}")
        if report["imports"].get("import_error"):
            print(f"Import error: {report['imports']['import_error']}")
        print(f"Torch: {report['torch'].get('version')} cuda_available={report['torch'].get('cuda_available')} devices={report['torch'].get('cuda_device_count')}")
        if report["cli"]:
            print(f"CLI on PATH: {report['cli'].get('executable_found')}")
            for name in ("root_help", "registry_models"):
                item = report["cli"].get(name)
                if item:
                    print(f"{name}: {'ok' if item.get('ok') else 'failed'}")
        for note in report["notes"]:
            print(f"NOTE: {note}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Safe MetaGPT environment diagnostic.

This helper checks package metadata, selected imports, CLI help availability,
and common configuration-placeholder symptoms. It does not call an LLM, browse
the web, generate a project, download datasets, or mutate configuration files.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_IMPORTS = [
    "metagpt",
    "metagpt.software_company",
    "metagpt.configs.llm_config",
    "metagpt.rag.interface",
]
CONFIG_IMPORTS = [
    "metagpt.config2",
    "metagpt.roles.role",
    "metagpt.actions.action",
    "metagpt.roles.di.data_interpreter",
]


def result(ok: bool, **kwargs: Any) -> dict[str, Any]:
    return {"ok": ok, **kwargs}


def dist_info() -> dict[str, Any]:
    try:
        version = metadata.version("metagpt")
        dist = metadata.distribution("metagpt")
        requires = dist.requires or []
        return result(True, version=version, requires_count=len(requires))
    except Exception as exc:
        return result(False, error=f"{type(exc).__name__}: {exc}")


def import_check(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        path = getattr(module, "__file__", None)
        return result(True, module=name, file=path)
    except Exception as exc:
        message = str(exc)
        hint = None
        if "YOUR_API_KEY" in message or "api_key" in message:
            hint = "MetaGPT config validation failed; replace placeholder keys in ~/.metagpt/config2.yaml or the active config."
        elif isinstance(exc, ModuleNotFoundError):
            hint = "Install the missing base or workflow-specific optional dependency."
        return result(False, module=name, error=f"{type(exc).__name__}: {message}", hint=hint)


def cli_help(timeout: float) -> dict[str, Any]:
    exe = shutil.which("metagpt")
    command = [exe or "metagpt", "--help"]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        output = (proc.stdout or proc.stderr or "")[:4000]
        return result(proc.returncode == 0, command=" ".join(command), returncode=proc.returncode, output=output)
    except FileNotFoundError:
        return result(False, command="metagpt --help", error="metagpt executable not found on PATH")
    except subprocess.TimeoutExpired:
        return result(False, command="metagpt --help", error=f"timed out after {timeout} seconds")


def signature_check() -> dict[str, Any]:
    data: dict[str, Any] = {}
    try:
        from metagpt.software_company import generate_repo, startup

        data["generate_repo"] = str(inspect.signature(generate_repo))
        data["startup"] = str(inspect.signature(startup))
        return result(True, signatures=data)
    except Exception as exc:
        return result(False, signatures=data, error=f"{type(exc).__name__}: {exc}")


def config_file_hints() -> dict[str, Any]:
    candidates = [Path.home() / ".metagpt" / "config2.yaml"]
    project_root = os.environ.get("METAGPT_PROJECT_ROOT")
    if project_root:
        candidates.append(Path(project_root) / "config" / "config2.yaml")
    found = []
    for path in candidates:
        try:
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
                found.append(
                    {
                        "path_kind": "home-config" if path.parent.name == ".metagpt" else "project-config",
                        "exists": True,
                        "contains_placeholder_key": "YOUR_API_KEY" in text,
                    }
                )
        except Exception as exc:
            found.append({"path_kind": "unknown", "exists": True, "error": f"{type(exc).__name__}: {exc}"})
    return result(True, configs=found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect a MetaGPT Python environment.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--include-config-imports", action="store_true", help="Also import modules that may instantiate Config.default().")
    parser.add_argument("--skip-cli", action="store_true", help="Skip metagpt --help check.")
    parser.add_argument("--timeout", type=float, default=15.0, help="CLI help timeout in seconds.")
    args = parser.parse_args(argv)

    imports = list(DEFAULT_IMPORTS)
    if args.include_config_imports:
        imports.extend(CONFIG_IMPORTS)

    report = {
        "python": sys.version.split()[0],
        "distribution": dist_info(),
        "imports": [import_check(name) for name in imports],
        "signatures": signature_check(),
        "config_files": config_file_hints(),
        "cli_help": None if args.skip_cli else cli_help(args.timeout),
    }
    ok = bool(report["distribution"].get("ok")) and all(item.get("ok") for item in report["imports"])
    if report["cli_help"] is not None:
        ok = ok and bool(report["cli_help"].get("ok"))
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"MetaGPT environment ok: {ok}")
        print(f"Python: {report['python']}")
        print(f"Distribution: {report['distribution']}")
        for item in report["imports"]:
            status = "OK" if item.get("ok") else "FAIL"
            print(f"{status}: {item.get('module')} {item.get('error', '')} {item.get('hint', '')}")
        if report["cli_help"] is not None:
            print(f"CLI help: {'OK' if report['cli_help'].get('ok') else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

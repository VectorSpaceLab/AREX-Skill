#!/usr/bin/env python3
"""Safe Optimum CLI probe.

This script inspects the installed Optimum CLI without mutating package files,
exporting models, downloading assets, or requiring credentials. It adapts the
source CLI registration test into read-only checks for help routing and
namespace registration conventions.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence


def _build_cli_command() -> tuple[list[str], str]:
    cli = shutil.which("optimum-cli")
    if cli:
        return [cli], "console-script"
    return [sys.executable, "-m", "optimum.commands.optimum_cli"], "python-module"


def _run(command: Sequence[str], timeout: float) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            list(command),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout} seconds.",
        }


def _contains_command(help_text: str, command_name: str) -> bool:
    return re.search(rf"(^|\n)\s*{re.escape(command_name)}\b", help_text) is not None or re.search(
        rf"\b{re.escape(command_name)}\b", help_text
    ) is not None


def _excerpt(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _inspect_register_namespace() -> Dict[str, Any]:
    spec = importlib.util.find_spec("optimum.commands.register")
    if spec is None or spec.submodule_search_locations is None:
        return {
            "namespace_found": False,
            "location_count": 0,
            "modules": [],
            "has_init_file": False,
            "note": "No optimum.commands.register namespace was found in this environment.",
        }

    modules: List[str] = []
    has_init = False
    location_count = 0
    for location in sorted(set(str(p) for p in spec.submodule_search_locations)):
        path = Path(location)
        if not path.is_dir():
            continue
        location_count += 1
        has_init = has_init or (path / "__init__.py").exists()
        modules.extend(sorted(p.stem for p in path.iterdir() if p.suffix == ".py" and p.name != "__init__.py"))

    return {
        "namespace_found": True,
        "location_count": location_count,
        "modules": sorted(set(modules)),
        "has_init_file": has_init,
        "note": "Registration modules should define REGISTER_COMMANDS and remain lightweight at import time.",
    }


def _diagnose(report: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
    root = report.get("root_help", {})
    export = report.get("export_help", {})
    if not root.get("ok"):
        notes.append("Base CLI help did not run. Check that Optimum is installed in the active Python environment.")
    else:
        if not report.get("root_help_has_export") or not report.get("root_help_has_env"):
            notes.append("Root help did not show both expected base commands: export and env.")
        else:
            notes.append("Base CLI root commands are visible: export and env.")
    if export:
        if report.get("export_help_has_onnx"):
            notes.append("The ONNX export subcommand appears to be registered under optimum-cli export.")
        else:
            notes.append(
                "The ONNX export subcommand was not found in export help. This is expected for a base-only install; install the ONNX partner package for export onnx."
            )
    namespace = report.get("register_namespace", {})
    if namespace.get("has_init_file"):
        notes.append("A registration namespace contains __init__.py; PEP 420 namespace registration may be impaired.")
    return notes


def _make_report(args: argparse.Namespace) -> Dict[str, Any]:
    cli_cmd, command_source = _build_cli_command()
    report: Dict[str, Any] = {
        "script": "probe_optimum_cli.py",
        "safe_default": True,
        "command_source": command_source,
        "registration_contract": {
            "root_command": "REGISTER_COMMANDS = [MyCommand]",
            "export_subcommand": "REGISTER_COMMANDS = [(MyCommand, ExportCommand)]",
            "command_base": "Subclass BaseOptimumCLICommand and set COMMAND = CommandInfo(...).",
            "mutation": "This probe does not copy or write registration files.",
        },
    }

    root_result = _run([*cli_cmd, "--help"], timeout=args.timeout)
    report["root_help"] = {
        "ok": root_result["ok"],
        "returncode": root_result["returncode"],
        "stdout_excerpt": _excerpt(root_result["stdout"]),
        "stderr_excerpt": _excerpt(root_result["stderr"]),
    }
    report["root_help_has_export"] = _contains_command(root_result["stdout"], "export")
    report["root_help_has_env"] = _contains_command(root_result["stdout"], "env")

    if not args.no_export_help:
        export_result = _run([*cli_cmd, "export", "--help"], timeout=args.timeout)
        combined = export_result["stdout"] + "\n" + export_result["stderr"]
        report["export_help"] = {
            "ok": export_result["ok"],
            "returncode": export_result["returncode"],
            "stdout_excerpt": _excerpt(export_result["stdout"]),
            "stderr_excerpt": _excerpt(export_result["stderr"]),
        }
        report["export_help_has_onnx"] = re.search(r"\bonnx\b", combined, flags=re.IGNORECASE) is not None

    report["register_namespace"] = _inspect_register_namespace()

    if args.run_env:
        env_result = _run([*cli_cmd, "env"], timeout=args.timeout)
        report["env"] = {
            "ok": env_result["ok"],
            "returncode": env_result["returncode"],
            "stdout_excerpt": _excerpt(env_result["stdout"], limit=2000),
            "stderr_excerpt": _excerpt(env_result["stderr"], limit=1000),
        }

    report["diagnosis"] = _diagnose(report)
    return report


def _print_text(report: Dict[str, Any]) -> None:
    print("Optimum CLI probe")
    print(f"- command source: {report['command_source']}")
    print(
        "- root help: {ok} (export={export}, env={env})".format(
            ok="ok" if report["root_help"]["ok"] else "failed",
            export=report.get("root_help_has_export"),
            env=report.get("root_help_has_env"),
        )
    )
    if "export_help" in report:
        print(
            "- export help: {ok} (onnx subcommand seen={onnx})".format(
                ok="ok" if report["export_help"]["ok"] else "failed",
                onnx=report.get("export_help_has_onnx"),
            )
        )
    namespace = report["register_namespace"]
    print(
        "- register namespace: found={found}, locations={count}, modules={modules}, has_init_file={has_init}".format(
            found=namespace["namespace_found"],
            count=namespace["location_count"],
            modules=namespace["modules"],
            has_init=namespace["has_init_file"],
        )
    )
    if "env" in report:
        print(f"- env command: {'ok' if report['env']['ok'] else 'failed'}")
        if report["env"]["stdout_excerpt"]:
            print("\n[env excerpt]")
            print(report["env"]["stdout_excerpt"])
    print("\nDiagnosis:")
    for note in report["diagnosis"]:
        print(f"- {note}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inspect Optimum CLI help, env, and registration state.")
    parser.add_argument("--run-env", action="store_true", help="Also run `optimum-cli env`.")
    parser.add_argument("--no-export-help", action="store_true", help="Skip `optimum-cli export --help`.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict-base", action="store_true", help="Exit nonzero if base root help lacks export/env.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout in seconds for each CLI command.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = _make_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)

    if args.strict_base:
        root_ok = report["root_help"].get("ok") and report.get("root_help_has_export") and report.get("root_help_has_env")
        return 0 if root_ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

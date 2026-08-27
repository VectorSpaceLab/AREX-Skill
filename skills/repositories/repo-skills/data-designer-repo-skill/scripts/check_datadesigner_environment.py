#!/usr/bin/env python3
"""Read-only smoke check for a DataDesigner installation.

This helper is safe to run from any working directory. It verifies the active
Python environment, package versions, core imports, CLI help, agent context, and
one sampler-only validation smoke.

Example:
    python scripts/check_datadesigner_environment.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any


def _run(cmd: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return {
        "command": cmd,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _tail(text: str, limit: int = 24) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-limit:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    parser.add_argument("--skip-cli", action="store_true", help="Skip CLI help/context checks")
    parser.add_argument("--skip-validation", action="store_true", help="Skip the sampler-only validation smoke")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "versions": {},
        "imports": {},
        "commands": [],
        "validation": None,
    }

    try:
        import data_designer.config as dd
        from data_designer.interface import DataDesigner

        smoke_provider = dd.ModelProvider(
            name="smoke-provider",
            endpoint="http://127.0.0.1:9/v1",
            provider_type="openai",
            api_key="DUMMY",
        )

        report["imports"]["data_designer.config"] = True
        report["imports"]["data_designer.interface"] = True
        report["versions"]["data-designer"] = version("data-designer")
        report["versions"]["data-designer-config"] = version("data-designer-config")
        report["versions"]["data-designer-engine"] = version("data-designer-engine")

        if not args.skip_validation:
            builder = dd.DataDesignerConfigBuilder(model_configs=[])
            builder.add_column(
                dd.SamplerColumnConfig(
                    name="uid",
                    sampler_type=dd.SamplerType.UUID,
                    params=dd.UUIDSamplerParams(prefix="u-"),
                )
            )
            data_designer = DataDesigner(model_providers=[smoke_provider], auto_configure_logging=False)
            data_designer.validate(builder)
            report["validation"] = "passed"

    except Exception as exc:  # pragma: no cover - report only
        report["imports"]["error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if not args.skip_cli:
        cli_help = _run([sys.executable, "-m", "data_designer.cli.main", "--help"])
        agent_context = _run([sys.executable, "-m", "data_designer.cli.main", "agent", "context"])
        report["commands"].append({"name": "data-designer --help", **cli_help, "stdout_tail": _tail(cli_help["stdout"])})
        report["commands"].append({"name": "data-designer agent context", **agent_context, "stdout_tail": _tail(agent_context["stdout"])})

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['executable']}")
        print(f"Version: {report['python']['version'].splitlines()[0]}")
        for name, value in report["versions"].items():
            print(f"{name}: {value}")
        print(f"Validation: {report['validation']}")
        if report["commands"]:
            for command in report["commands"]:
                print(f"--- {command['name']} (exit {command['exit_code']})")
                for line in command["stdout_tail"]:
                    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

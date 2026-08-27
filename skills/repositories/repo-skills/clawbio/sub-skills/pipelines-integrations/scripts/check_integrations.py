#!/usr/bin/env python3
"""Safe, non-starting diagnostics for ClawBio integrations.

This checker reports Python module discoverability and executable availability.
It never loads secrets, contacts a provider, starts a service, opens a socket,
pulls a container, or runs a Nextflow pipeline. ``--pipeline-help`` only asks
the ClawBio parser to render wrapper help and should exit before execution.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

# A checkout invocation normally places the script directory, not the caller's
# working directory, on sys.path. Add the caller directory only for discoverability
# checks; no source path is embedded in the skill or required at runtime.
if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

OPTIONAL_MODULES = {
    "mcp-sdk": "mcp",
    "telegram": "telegram",
    "discord": "discord",
    "flask": "flask",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "requests": "requests",
    "dotenv": "dotenv",
    "openai": "openai",
    "yaml": "yaml",
}
SAFE_MODULES = {
    "mcp-core": "clawbio.mcp_server",
    "bot-security": "bot.security",
    "bot-tool-loop": "bot.tool_loop_utils",
    "robotary-server": "robotary.server",
}
BINARIES = (
    "python3",
    "java",
    "nextflow",
    "docker",
    "podman",
    "singularity",
    "apptainer",
    "conda",
    "mamba",
    "ffmpeg",
    "edge-tts",
)
PIPELINES = ("scrnaseq-pipeline", "rnaseq-pipeline", "sarek-pipeline")


def _module_status(module: str) -> dict[str, object]:
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        return {"available": False, "detail": f"{type(exc).__name__}: {exc}"}
    return {
        "available": spec is not None,
        "detail": "available" if spec else "not found",
    }


def _binary_status(binary: str) -> dict[str, object]:
    path = shutil.which(binary)
    return {"available": path is not None, "detail": "available" if path else "not found"}


def _pipeline_help(pipeline: str) -> dict[str, object]:
    if pipeline not in PIPELINES:
        return {"ok": False, "error": f"unsupported pipeline: {pipeline}"}
    executable = shutil.which("clawbio")
    command = [executable, "run", pipeline, "--help"] if executable else [
        sys.executable, "-m", "clawbio.cli", "run", pipeline, "--help"
    ]
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "command": command, "error": f"{type(exc).__name__}: {exc}"}
    output = (proc.stdout or proc.stderr or "")
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": command,
        "contains_usage": "usage" in output.lower(),
        "output_tail": output[-500:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check ClawBio integration imports and binaries without starting services or pipelines."
    )
    parser.add_argument(
        "--pipeline-help",
        choices=PIPELINES,
        action="append",
        help="Render one wrapper's help through clawbio; no Nextflow run is started.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report: dict[str, object] = {
        "safe": True,
        "services_started": False,
        "network_used": False,
        "credentials_read": False,
        "optional_modules": {
            name: _module_status(module) for name, module in OPTIONAL_MODULES.items()
        },
        "safe_module_specs": {
            name: _module_status(module) for name, module in SAFE_MODULES.items()
        },
        "binaries": {name: _binary_status(name) for name in BINARIES},
    }
    if args.pipeline_help:
        report["pipeline_help"] = {
            pipeline: _pipeline_help(pipeline) for pipeline in args.pipeline_help
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ClawBio integration diagnostics (non-starting)")
        print("  services started: no; network used: no; credentials read: no")
        print("\nOptional Python modules:")
        for name, status in report["optional_modules"].items():
            print(f"  {'OK ' if status['available'] else 'MISS'} {name}: {status['detail']}")
        print("\nSafe module discoverability:")
        for name, status in report["safe_module_specs"].items():
            print(f"  {'OK ' if status['available'] else 'MISS'} {name}: {status['detail']}")
        print("\nExecutables:")
        for name, status in report["binaries"].items():
            print(f"  {'OK ' if status['available'] else 'MISS'} {name}: {status['detail']}")
        for pipeline, result in report.get("pipeline_help", {}).items():
            print(f"\n{pipeline} --help: {'OK' if result.get('ok') else 'FAILED'}")
            if result.get("output_tail"):
                print(result["output_tail"].rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

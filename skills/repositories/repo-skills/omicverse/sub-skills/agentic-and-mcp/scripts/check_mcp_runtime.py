#!/usr/bin/env python3
"""Safe OmicVerse MCP/CLI runtime checker.

This script performs read-only import, version, public-API, and CLI help
checks. It does not start MCP transports, network listeners, JARVIS channels,
or long-running services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import shutil
import subprocess
import sys
from typing import Any

VALID_PROFILES = ("fast-mock", "core-runtime", "scientific-runtime", "extended-runtime")

PROFILE_PACKAGES = {
    "fast-mock": ["omicverse", "numpy", "pandas", "pytest", "pytest-asyncio"],
    "core-runtime": ["omicverse", "anndata", "scanpy", "numpy", "pandas", "scipy", "matplotlib"],
    "scientific-runtime": [
        "omicverse",
        "anndata",
        "scanpy",
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "scvelo",
        "squidpy",
    ],
    "extended-runtime": [
        "omicverse",
        "anndata",
        "scanpy",
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "scvelo",
        "squidpy",
        "pertpy",
        "SEACells",
        "mira-multiome",
    ],
}

EXPECTED_MCP_FLAGS = (
    "--phase",
    "--transport",
    "--session-id",
    "--persist-dir",
    "--max-adata",
    "--max-artifacts",
    "--host",
    "--port",
    "--http-path",
)

EXPECTED_ROOT_COMMANDS = ("claw", "jarvis", "web", "gateway", "skill-seeker")
EXPECTED_SKILL_SEEKER_FLAGS = (
    "--list",
    "--validate",
    "--package",
    "--package-all",
    "--create-from-link",
    "--build-config",
)


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except Exception:
        return None


def run_help(command: list[str], timeout: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "command": command, "error": str(exc), "returncode": None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": command, "error": f"timed out after {timeout}s", "returncode": None}

    return {
        "ok": proc.returncode == 0,
        "command": command,
        "returncode": proc.returncode,
        "stdout_excerpt": proc.stdout[:2000],
        "stderr_excerpt": proc.stderr[:2000],
    }


def contains_all(text: str, expected: tuple[str, ...]) -> dict[str, bool]:
    return {item: item in text for item in expected}


def inspect_mcp_public_api() -> dict[str, Any]:
    result: dict[str, Any] = {"import_ok": False}
    try:
        mcp = importlib.import_module("omicverse.mcp")
        result["import_ok"] = True
        result["public_api"] = {name: hasattr(mcp, name) for name in ("build_default_manifest", "build_mcp_server", "get_manifest")}
        manifest = mcp.get_manifest(phase="P0")
        result["p0_manifest_count"] = len(manifest)
        result["p0_first_tools"] = [entry.get("tool_name") for entry in manifest[:10]]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    package_versions = {pkg: package_version(pkg) for pkg in PROFILE_PACKAGES[args.profile]}
    executables = {name: shutil.which(name) is not None for name in ("omicverse", "omicverse-mcp", "ov-skill-seeker")}

    cli_checks: dict[str, Any] = {}
    if not args.skip_cli:
        commands = {
            "omicverse_help": ["omicverse", "--help"],
            "omicverse_mcp_help": ["omicverse-mcp", "--help"],
            "python_module_mcp_help": [sys.executable, "-m", "omicverse.mcp", "--help"],
            "ov_skill_seeker_help": ["ov-skill-seeker", "--help"],
        }
        for key, command in commands.items():
            cli_checks[key] = run_help(command, timeout=args.timeout)

        root_stdout = cli_checks.get("omicverse_help", {}).get("stdout_excerpt", "")
        mcp_stdout = cli_checks.get("omicverse_mcp_help", {}).get("stdout_excerpt", "")
        module_mcp_stdout = cli_checks.get("python_module_mcp_help", {}).get("stdout_excerpt", "")
        seeker_stdout = cli_checks.get("ov_skill_seeker_help", {}).get("stdout_excerpt", "")

        cli_checks["expected_root_commands"] = contains_all(root_stdout, EXPECTED_ROOT_COMMANDS)
        cli_checks["expected_mcp_flags"] = contains_all(mcp_stdout or module_mcp_stdout, EXPECTED_MCP_FLAGS)
        cli_checks["expected_skill_seeker_flags"] = contains_all(seeker_stdout, EXPECTED_SKILL_SEEKER_FLAGS)

    return {
        "schema_version": 1,
        "profile": args.profile,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": package_versions,
        "executables_on_path": executables,
        "mcp_public_api": inspect_mcp_public_api(),
        "cli_checks": cli_checks,
        "safe_defaults": {
            "starts_services": False,
            "opens_network_listener": False,
            "contacts_llm_provider": False,
            "reads_user_credentials": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check OmicVerse MCP/CLI runtime without starting services.")
    parser.add_argument("--profile", choices=VALID_PROFILES, default="fast-mock", help="Dependency profile to report.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for help subprocesses.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip subprocess help checks and only inspect imports/versions.")
    parser.add_argument("--output", default=None, help="Optional JSON output file path. Defaults to stdout.")
    args = parser.parse_args(argv)

    report = build_report(args)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe LeptonAI package and CLI smoke check.

The default check imports the package and, when `lep` is available, runs only
help/version commands. It strips common credential environment variables from
subprocesses and never contacts a Lepton workspace intentionally.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_GROUPS = ["endpoint", "workspace", "job", "pod", "ingress", "storage"]
STRIP_PREFIXES = ("LEP_",)
STRIP_NAMES = {
    "LEPTON_WORKSPACE_ID",
    "LEPTON_WORKSPACE_TOKEN",
    "LEPTON_WORKSPACE_URL",
    "LEPTON_WORKSPACE_ORIGIN_URL",
    "LEPTON_API_TOKEN",
    "LEPTON_API_URL",
}


def sanitized_env(cache_dir: str) -> dict:
    env = {}
    for key, value in os.environ.items():
        if key in STRIP_NAMES:
            continue
        if any(key.startswith(prefix) for prefix in STRIP_PREFIXES):
            continue
        env[key] = value
    env["LEPTON_CACHE_DIR"] = cache_dir
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    return env


def run_command(args: List[str], timeout: float, env: dict, display_args: Optional[List[str]] = None) -> dict:
    shown = display_args or args
    try:
        completed = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        return {
            "args": shown,
            "exit_code": completed.returncode,
            "ok": completed.returncode == 0,
            "timed_out": False,
            "output_excerpt": completed.stdout[:1000],
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        return {
            "args": shown,
            "exit_code": None,
            "ok": False,
            "timed_out": True,
            "output_excerpt": out[:1000],
        }
    except OSError as exc:
        return {
            "args": shown,
            "exit_code": 127,
            "ok": False,
            "timed_out": False,
            "output_excerpt": f"unable to execute: {exc}",
        }


def package_check() -> dict:
    result: Dict[str, Any] = {"ok": False}
    try:
        version = metadata.version("leptonai")
    except metadata.PackageNotFoundError:
        result["error"] = "distribution metadata for leptonai was not found"
        return result
    try:
        module = importlib.import_module("leptonai")
        from leptonai.client import Client, local  # noqa: F401
        from leptonai.api.v2.spec_utils import make_mounts_from_strings

        mount = make_mounts_from_strings(["/data:/mnt/data:node-local"])[0]
        result.update(
            {
                "ok": True,
                "distribution_version": version,
                "module_version": getattr(module, "__version__", None),
                "local_8080": local(8080),
                "mount_volume": getattr(mount, "from_", None),
            }
        )
    except Exception as exc:
        result.update({"error": f"import or smoke failed: {exc.__class__.__name__}: {exc}"})
    return result


def cli_check(lep: str, groups: Iterable[str], timeout: float) -> dict:
    lep_path = shutil.which(lep) if os.path.basename(lep) == lep else lep
    if not lep_path:
        return {"ok": False, "error": "lep executable not found on PATH"}
    with tempfile.TemporaryDirectory(prefix="leptonai-smoke-cache-") as cache_dir:
        env = sanitized_env(cache_dir)
        commands = [([lep_path, "--version"], ["lep", "--version"]), ([lep_path, "--help"], ["lep", "--help"])]
        commands.extend(([lep_path, group, "--help"], ["lep", group, "--help"]) for group in groups)
        runs = [run_command(command, timeout, env, display) for command, display in commands]
    return {"ok": all(run["ok"] for run in runs), "runs": runs}


def print_text(result: dict) -> None:
    print("LeptonAI smoke check")
    print(f"package: {'ok' if result['package']['ok'] else 'failed'}")
    if result["package"].get("distribution_version"):
        print(f"version: {result['package']['distribution_version']}")
    if result.get("cli"):
        cli = result["cli"]
        print(f"cli: {'ok' if cli.get('ok') else 'failed'}")
        for run in cli.get("runs", []):
            rendered = " ".join(run["args"])
            print(f"  $ {rendered} -> {run['exit_code']}{' timeout' if run['timed_out'] else ''}")
        if cli.get("error"):
            print(f"  error: {cli['error']}")
    if result.get("ok"):
        print("status: ok")
    else:
        print("status: failed")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run safe LeptonAI import and CLI help checks.")
    parser.add_argument("--skip-cli", action="store_true", help="Only run Python import/package checks.")
    parser.add_argument("--lep", default="lep", help="CLI executable name or path; default: lep")
    parser.add_argument("--groups", nargs="*", default=DEFAULT_GROUPS, help="CLI groups to inspect with --help.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds per CLI help command.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    result: Dict[str, Any] = {"package": package_check()}
    if not args.skip_cli:
        result["cli"] = cli_check(args.lep, args.groups, args.timeout)
    result["ok"] = result["package"].get("ok") and (args.skip_cli or result.get("cli", {}).get("ok"))

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

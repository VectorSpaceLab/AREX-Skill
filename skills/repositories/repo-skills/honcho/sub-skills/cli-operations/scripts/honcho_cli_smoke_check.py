#!/usr/bin/env python3
"""Safe local smoke checks for the Honcho CLI.

The checks avoid network calls by using an isolated temporary config directory
and only exercising version/help/config output plus validation that fails before
client construction.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _base_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("HONCHO_"):
            env.pop(key, None)
    env["HONCHO_JSON"] = "1"
    return env


def _run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def check_honcho_on_path(honcho: str) -> Check:
    path = shutil.which(honcho)
    if not path:
        return Check("honcho executable", False, f"{honcho!r} not found on PATH")
    return Check("honcho executable", True, path)


def check_version(honcho: str, env: dict[str, str]) -> Check:
    proc = _run([honcho, "--version"], env)
    ok = proc.returncode == 0 and "honcho-cli" in (proc.stdout + proc.stderr)
    return Check("version", ok, (proc.stdout + proc.stderr).strip())


def check_group_help(honcho: str, env: dict[str, str], group: str) -> Check:
    proc = _run([honcho, group, "--help"], env)
    text = proc.stdout + proc.stderr
    # Command groups include a Commands panel; leaf commands such as doctor do not.
    ok = proc.returncode == 0 and f"honcho {group}" in text
    return Check(f"{group} help", ok, text.strip().splitlines()[0] if text.strip() else "empty help")


def check_config_json(honcho: str, env: dict[str, str]) -> Check:
    proc = _run([honcho, "config", "--json"], env)
    if proc.returncode != 0:
        return Check("config json", False, proc.stderr.strip())
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return Check("config json", False, f"invalid JSON: {exc}: {proc.stdout!r}")
    ok = payload.get("base_url") == "https://api.honcho.dev"
    return Check("config json", ok, json.dumps(payload, sort_keys=True))


def check_structured_validation(honcho: str, env: dict[str, str]) -> Check:
    proc = _run(
        [honcho, "message", "list", "sess1", "--last", "0", "-w", "ws1", "--json"],
        env,
    )
    if proc.returncode == 0:
        return Check("structured validation", False, "expected non-zero exit")
    try:
        payload = json.loads(proc.stderr)
    except json.JSONDecodeError as exc:
        return Check("structured validation", False, f"stderr not JSON: {exc}: {proc.stderr!r}")
    code = payload.get("error", {}).get("code")
    return Check("structured validation", code == "INVALID_FLAGS", code or repr(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--honcho", default="honcho", help="Honcho executable name/path")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable check results instead of a short text report.",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="honcho-cli-smoke-") as tmp:
        env = _base_env()
        env["HONCHO_CONFIG_DIR"] = tmp
        checks = [check_honcho_on_path(args.honcho)]
        if checks[0].ok:
            checks.extend(
                [
                    check_version(args.honcho, env),
                    check_group_help(args.honcho, env, "doctor"),
                    check_group_help(args.honcho, env, "workspace"),
                    check_group_help(args.honcho, env, "peer"),
                    check_group_help(args.honcho, env, "session"),
                    check_group_help(args.honcho, env, "message"),
                    check_group_help(args.honcho, env, "conclusion"),
                    check_config_json(args.honcho, env),
                    check_structured_validation(args.honcho, env),
                ]
            )

    passed = sum(1 for check in checks if check.ok)
    result = {
        "checks": [check.__dict__ for check in checks],
        "passed": passed,
        "total": len(checks),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for check in checks:
            marker = "ok" if check.ok else "FAIL"
            print(f"[{marker}] {check.name}: {check.detail}")
        print(f"{passed}/{len(checks)} checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

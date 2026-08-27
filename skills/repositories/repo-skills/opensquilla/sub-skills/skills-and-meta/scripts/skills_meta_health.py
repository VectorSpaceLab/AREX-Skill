#!/usr/bin/env python3
"""Read-only OpenSquilla Skill/MetaSkill health snapshot.

This helper intentionally avoids mutating commands. It does not install,
update, uninstall, reload, publish, search, or accept proposals.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def _run(command: list[str], *, timeout: float) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "command": command,
            "exit_code": 127,
            "ok": False,
            "error": str(exc),
            "stdout": "",
            "stderr": "",
            "json": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "ok": False,
            "error": f"timeout after {timeout:.1f}s",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "json": None,
        }

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    parsed: Any = None
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": command,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "error": "",
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only snapshot of OpenSquilla Skill and MetaSkill state.",
    )
    parser.add_argument(
        "--opensquilla",
        default="opensquilla",
        help="OpenSquilla executable name or path on PATH (default: opensquilla).",
    )
    parser.add_argument(
        "--skill",
        default="",
        help="Optional Skill name or install id to pass to skills doctor.",
    )
    parser.add_argument(
        "--meta",
        default="",
        help="Optional MetaSkill name to inspect with skills inspect.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-command timeout in seconds (default: 20).",
    )
    args = parser.parse_args(argv)

    executable = shutil.which(args.opensquilla) or args.opensquilla
    if shutil.which(args.opensquilla) is None and args.opensquilla == "opensquilla":
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "opensquilla executable not found on PATH",
                    "commands": [],
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
        return 1

    commands: list[tuple[str, list[str]]] = [
        ("skills_list", [executable, "skills", "list", "--json"]),
        (
            "skills_doctor",
            [executable, "skills", "doctor"]
            + ([args.skill] if args.skill else [])
            + ["--json"],
        ),
        (
            "meta_runs_recent",
            [
                executable,
                "skills",
                "meta",
                "runs",
                "list",
                "--limit",
                "5",
                "--json",
            ],
        ),
        (
            "meta_proposals",
            [executable, "skills", "meta", "proposals", "list", "--json"],
        ),
    ]
    if args.meta:
        commands.append(("meta_inspect", [executable, "skills", "inspect", args.meta]))

    results = {label: _run(cmd, timeout=args.timeout) for label, cmd in commands}
    payload = {
        "ok": all(item["ok"] for item in results.values()),
        "read_only": True,
        "mutating_commands_excluded": [
            "skills install",
            "skills update",
            "skills uninstall",
            "skills reload",
            "skills publish",
            "skills search",
            "skills meta proposals accept",
        ],
        "results": results,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

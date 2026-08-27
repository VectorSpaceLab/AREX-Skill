#!/usr/bin/env python3
"""Inspect Lepton workspace auth context without exposing token values.

Default mode reports only environment-variable presence and consistency hints.
With --run-cli, the script runs selected read-only `lep workspace` commands,
captures their output, and redacts token-looking values before printing.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import Iterable, List, Optional, Sequence
from urllib.parse import urlsplit, urlunsplit

ENV_VARS = (
    "LEPTON_WORKSPACE_ID",
    "LEPTON_WORKSPACE_TOKEN",
    "LEPTON_WORKSPACE_URL",
    "LEPTON_WORKSPACE_ORIGIN_URL",
)

SECRET_ENV_VARS = {"LEPTON_WORKSPACE_TOKEN"}
DEFAULT_COMMANDS = ("list", "status", "id", "url")
TOKEN_PLACEHOLDER = "<redacted-token>"


def _mask_short(value: str) -> str:
    if not value:
        return "<empty>"
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}****{value[-2:]}"


def _safe_url(value: Optional[str]) -> str:
    if not value:
        return "<unset>"
    try:
        parts = urlsplit(value)
    except Exception:
        return "<set:unparseable>"
    netloc = parts.hostname or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    # Drop username, password, query, and fragment. Workspace id in path is kept
    # because URL mismatch diagnosis often depends on it.
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def _summarize_env(show_non_secret_values: bool) -> None:
    print("Environment context:")
    values = {name: os.environ.get(name) for name in ENV_VARS}
    for name in ENV_VARS:
        value = values[name]
        if value is None:
            rendered = "unset"
        elif name in SECRET_ENV_VARS:
            rendered = f"set ({TOKEN_PLACEHOLDER}; mask={_mask_short(value)})"
        elif show_non_secret_values:
            rendered = f"set ({_safe_url(value) if name.endswith('_URL') else value})"
        else:
            rendered = "set"
        print(f"  - {name}: {rendered}")

    print("\nConsistency hints:")
    hints: List[str] = []
    if values["LEPTON_WORKSPACE_TOKEN"] and not values["LEPTON_WORKSPACE_ID"]:
        hints.append("token is set but workspace id is unset; APIClient() still needs a workspace id or current record")
    if values["LEPTON_WORKSPACE_URL"] and not values["LEPTON_WORKSPACE_ID"]:
        hints.append("workspace URL is set but workspace id is unset; this can combine with an unintended persisted record")
    if values["LEPTON_WORKSPACE_ORIGIN_URL"] and not values["LEPTON_WORKSPACE_URL"]:
        hints.append("origin URL is set without workspace URL; verify this advanced override is intentional")
    if values["LEPTON_WORKSPACE_ID"] and not values["LEPTON_WORKSPACE_TOKEN"]:
        hints.append("workspace id is set but token is unset; Python may fall back to a persisted token only if a matching record exists")
    if (
        values["LEPTON_WORKSPACE_URL"]
        and values["LEPTON_WORKSPACE_ORIGIN_URL"]
        and values["LEPTON_WORKSPACE_URL"] != values["LEPTON_WORKSPACE_ORIGIN_URL"]
    ):
        hints.append("workspace URL and origin URL differ; verify that this is required by the target Lepton environment")
    if not hints:
        hints.append("no obvious environment-only mismatch detected")
    for hint in hints:
        print(f"  - {hint}")


def _token_values_from_env() -> List[str]:
    values = []
    for name in SECRET_ENV_VARS:
        value = os.environ.get(name)
        if value:
            values.append(value)
    return values


def _redact(text: str, extra_tokens: Iterable[str] = ()) -> str:
    redacted = text
    for token in list(_token_values_from_env()) + [t for t in extra_tokens if t]:
        redacted = redacted.replace(token, TOKEN_PLACEHOLDER)

    patterns = [
        (r"(?i)(Authorization\s*[:=]\s*Bearer\s+)(\S+)", r"\1" + TOKEN_PLACEHOLDER),
        (r"(?i)(Bearer\s+)([A-Za-z0-9._~+/=-]{8,})", r"\1" + TOKEN_PLACEHOLDER),
        (r"(?i)(auth[_-]?token\s*[:=]\s*)([^\s,'\")]+)", r"\1" + TOKEN_PLACEHOLDER),
        (r"(?i)(LEPTON_WORKSPACE_TOKEN\s*[:=]\s*)([^\s,'\")]+)", r"\1" + TOKEN_PLACEHOLDER),
        (r"(?i)(workspace token\s*[:=]\s*)([^\s,'\")]+)", r"\1" + TOKEN_PLACEHOLDER),
        # Credential strings. Keep the workspace id and redact only the token-like suffix.
        (r"\b([A-Za-z0-9_.-]{2,}):([A-Za-z0-9._~+/=-]{8,})\b", r"\1:" + TOKEN_PLACEHOLDER),
    ]
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def _run_cli(lep_bin: str, commands: Sequence[str], timeout: float) -> int:
    if shutil.which(lep_bin) is None:
        print(f"\nCLI checks skipped: could not find executable {lep_bin!r} on PATH.")
        return 127

    print(
        "\nRunning selected read-only `lep workspace` commands. "
        "These may contact Lepton APIs and use local credentials; output is redacted."
    )
    worst_exit = 0
    for command in commands:
        argv = [lep_bin, "workspace", command]
        print(f"\n$ {' '.join(argv)}")
        try:
            completed = subprocess.run(
                argv,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            print(f"exit: timeout after {timeout:g}s")
            partial = "\n".join(
                part for part in [exc.stdout or "", exc.stderr or ""] if part
            )
            if partial:
                print(_redact(partial))
            worst_exit = max(worst_exit, 124)
            continue

        print(f"exit: {completed.returncode}")
        if completed.stdout:
            print("stdout:")
            print(_redact(completed.stdout).rstrip())
        if completed.stderr:
            print("stderr:")
            print(_redact(completed.stderr).rstrip())
        if completed.returncode != 0 and worst_exit == 0:
            worst_exit = completed.returncode
    return worst_exit


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Lepton workspace env context and optionally run redacted read-only CLI checks."
    )
    parser.add_argument(
        "--run-cli",
        action="store_true",
        help="Run selected `lep workspace` read-only commands after env inspection.",
    )
    parser.add_argument(
        "--commands",
        nargs="+",
        choices=DEFAULT_COMMANDS,
        default=list(DEFAULT_COMMANDS),
        metavar="CMD",
        help="Workspace commands to run with --run-cli; choices: list, status, id, url.",
    )
    parser.add_argument(
        "--lep-bin",
        default=os.environ.get("LEP_BIN", "lep"),
        help="CLI executable name to use for --run-cli; defaults to `lep` or LEP_BIN.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-command timeout in seconds for --run-cli.",
    )
    parser.add_argument(
        "--show-non-secret-values",
        action="store_true",
        help="Print workspace id and sanitized URL values; token values remain redacted.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _summarize_env(show_non_secret_values=args.show_non_secret_values)
    if not args.run_cli:
        print("\nCLI checks not run. Add --run-cli to execute selected read-only workspace commands.")
        return 0
    return _run_cli(args.lep_bin, args.commands, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe DeepXiv CLI import/help/version smoke check.

This helper intentionally does not invoke a network command, resolve a token,
read a credential file, or write configuration. It uses the installed Python
package and Click's in-process runner, so it is safe to run from any cwd.
"""
from __future__ import annotations

import os
import sys

# cli.py conditionally loads .env files at import time. Disable that behavior
# before importing it so this smoke check remains credential-free.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"


def main() -> int:
    try:
        from click.testing import CliRunner
        import deepxiv_sdk
        from deepxiv_sdk.cli import main as cli_main
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"import check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    expected = {
        "agent",
        "ask",
        "biorxiv",
        "config",
        "debug",
        "health",
        "help",
        "medrxiv",
        "paper",
        "pmc",
        "search",
        "token",
        "trending",
    }
    actual = set(cli_main.commands)
    missing = sorted(expected - actual)
    if missing:
        print(f"CLI command check failed; missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    runner = CliRunner()
    checks = (
        (("--help",), "ask"),
        (("help",), "GET PAPER"),
        (("--version",), str(deepxiv_sdk.__version__)),
    )
    for args, marker in checks:
        result = runner.invoke(cli_main, list(args))
        if result.exit_code != 0:
            detail = type(result.exception).__name__ if result.exception else "unknown"
            print(f"{' '.join(args)} failed (exit {result.exit_code}, {detail})", file=sys.stderr)
            return 1
        if marker not in result.output:
            print(f"{' '.join(args)} output lacks expected marker {marker!r}", file=sys.stderr)
            return 1

    print(f"ok: imported deepxiv_sdk {deepxiv_sdk.__version__}")
    print("ok: CLI command registry and help/version smoke passed")
    print("safe: no network, credential read, token resolution, or config write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

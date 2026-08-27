#!/usr/bin/env python3
"""Safe smoke check for an Atomic Agents environment.

This helper verifies the public package import surface, the Atomic Assembler
entry point, and the MCP connector import path without contacting external
services or running repo-native examples.
"""

from __future__ import annotations

import importlib.metadata as md
import subprocess
import sys
from pathlib import Path


def _print(label: str, value: str) -> None:
    print(f"{label}: {value}")


def main() -> int:
    _print("python", sys.version.split()[0])
    _print("executable", sys.executable)

    import atomic_agents
    import atomic_assembler

    _print("atomic-agents", atomic_agents.__version__)
    _print("atomic-agents dist", md.version("atomic-agents"))
    _print("atomic_agents module", str(Path(atomic_agents.__file__).resolve()))
    _print("atomic_assembler module", str(Path(atomic_assembler.__file__).resolve()))

    # Import the MCP surface as a compatibility check. This is the part that is
    # most likely to drift when the `mcp` dependency line changes.
    from atomic_agents.connectors import mcp as atomic_mcp

    _print("mcp exports", ", ".join(atomic_mcp.__all__[:5]) + (" ..." if len(atomic_mcp.__all__) > 5 else ""))

    atomic_help = subprocess.run(["atomic", "--help"], capture_output=True, text=True, check=False)
    if atomic_help.returncode != 0:
        raise SystemExit(f"atomic --help failed with exit code {atomic_help.returncode}: {atomic_help.stderr.strip()}")

    first_help_line = next((line for line in atomic_help.stdout.splitlines() if line.strip()), "")
    _print("atomic --help", first_help_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

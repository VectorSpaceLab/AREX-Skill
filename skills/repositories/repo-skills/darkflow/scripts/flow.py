#!/usr/bin/env python3
"""Run Darkflow's installed CLI through the skill-owned wrapper.

Use this when the package is importable but the `flow` executable is not on PATH.
The script imports `darkflow.cli.cliHandler` from the installed package or from
an optional local checkout already present on PYTHONPATH.
"""

import sys

from darkflow.cli import cliHandler


if __name__ == "__main__":
    cliHandler(sys.argv)

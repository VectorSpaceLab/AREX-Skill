#!/usr/bin/env python3
"""Safe AXLearn install smoke check.

This script is intentionally read-only. It imports the installed AXLearn package,
prints a few public version facts, and confirms the main package can be located.

Example:
    python scripts/check_install.py
"""

from __future__ import annotations

from importlib import metadata


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "MISSING"


def main() -> int:
    import axlearn
    import axlearn.common.config
    import axlearn.common.launch_trainer_main
    import axlearn.cli.utils

    print(f"axlearn={_version('axlearn')}")
    print(f"jax={_version('jax')}")
    print(f"tensorflow={_version('tensorflow')}")
    print(f"axlearn module={axlearn.__file__}")
    print(f"config module={axlearn.common.config.__file__}")
    print(f"launcher module={axlearn.common.launch_trainer_main.__file__}")
    print(f"cli utils module={axlearn.cli.utils.__file__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

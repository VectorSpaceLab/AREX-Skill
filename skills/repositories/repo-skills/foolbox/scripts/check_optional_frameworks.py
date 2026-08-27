#!/usr/bin/env python3
"""Report optional Foolbox framework availability without importing Foolbox wrappers."""
from __future__ import annotations

import argparse
import importlib.util


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    for name in ("torch", "tensorflow", "jax"):
        available = importlib.util.find_spec(name) is not None
        print(f"{name}: {'available' if available else 'not installed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

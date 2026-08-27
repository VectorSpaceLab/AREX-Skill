#!/usr/bin/env python3
"""Smoke-check the installed pyts multivariate workflow.

Purpose: run the bundled pyts smoke helper for the multivariate-workflows
sub-skill from any current working directory without depending on the original
repository checkout.

Prerequisites: pyts must be installed in the active environment and the root
skill's shared smoke helper must be present in the same generated skill tree.
Example: python smoke.py
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Sequence

MODE = "multivariate"


def _load_root_helper():
    helper_path = Path(__file__).resolve().parents[3] / "scripts" / "pyts_smoke.py"
    spec = importlib.util.spec_from_file_location("pyts_skill_smoke", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load root smoke helper at {helper_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    parse_args(argv)
    helper = _load_root_helper()
    return helper.main(["--mode", MODE])


if __name__ == "__main__":
    raise SystemExit(main())

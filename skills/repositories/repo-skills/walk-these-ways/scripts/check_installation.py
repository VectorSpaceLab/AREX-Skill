#!/usr/bin/env python3
"""Read-only package and optional-backend diagnostic for Walk These Ways.

This helper never installs packages, imports Isaac Gym, constructs a simulator,
starts a logger, contacts a robot, or mutates the host. It reports import specs
and package metadata for the current Python interpreter.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from importlib import metadata
from typing import Dict, List, Optional

DISTRIBUTIONS = ["go1_gym", "torch", "numpy", "ml_logger", "ml_dash", "lcm", "netifaces"]
MODULES = ["go1_gym", "go1_gym_learn", "go1_gym_deploy", "torch", "isaacgym", "lcm"]


def version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)
    report: Dict[str, object] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": "<current-interpreter>",
        "distributions": {name: version(name) for name in DISTRIBUTIONS},
        "module_specs": {name: bool(importlib.util.find_spec(name)) for name in MODULES},
        "limits": [
            "module presence is not runtime verification",
            "isaacgym is not imported by this helper",
            "no installation, network, logger, simulator, or robot side effect",
        ],
    }
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print("Python:", report["python"])
        print("Distributions:")
        for name, value in report["distributions"].items():
            print("  {:12s} {}".format(name, value or "MISSING"))
        print("Module specs:")
        for name, present in report["module_specs"].items():
            print("  {:12s} {}".format(name, "present" if present else "MISSING"))
        print("Read-only diagnostic only; CUDA Torch does not prove Isaac Gym.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

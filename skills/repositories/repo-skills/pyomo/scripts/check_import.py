#!/usr/bin/env python3
"""Check that Pyomo imports from the active environment.

This helper is safe to run from any working directory. It prints the package
version and import locations for the base Pyomo package and `pyomo.environ`.
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text.",
    )
    args = parser.parse_args()

    import pyomo
    import pyomo.environ as pyo

    info = {
        "distribution": "pyomo",
        "version": metadata.version("pyomo"),
        "pyomo_file": pyomo.__file__,
        "environ_model": pyo.ConcreteModel.__name__,
    }

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        print(f"pyomo {info['version']}")
        print(info["pyomo_file"])
        print(pyo.ConcreteModel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

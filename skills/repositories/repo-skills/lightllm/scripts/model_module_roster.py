#!/usr/bin/env python3
"""List installed LightLLM model subpackages without importing model modules."""

from __future__ import annotations

import argparse
import importlib.util
import json
import pkgutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    spec = importlib.util.find_spec("lightllm.models")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("could not locate the installed lightllm.models package")

    roots = [Path(p) for p in spec.submodule_search_locations]
    modules = []
    for module_info in pkgutil.walk_packages([str(p) for p in roots], prefix="lightllm.models."):
        if module_info.name.count(".") <= 2:
            modules.append(module_info.name)

    modules = sorted(set(modules))
    info = {"package_roots": [str(p) for p in roots], "modules": modules}

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        for root in roots:
            print(f"root={root}")
        for name in modules:
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

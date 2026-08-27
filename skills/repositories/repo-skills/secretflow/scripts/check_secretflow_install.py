#!/usr/bin/env python3
"""Check that SecretFlow is importable and its core CLI/data surface is present.

This helper is intentionally small and side-effect free. It prints the installed
package version, the imported module path, and a few high-signal entry points
that are useful when validating a fresh environment.
"""

from importlib.metadata import PackageNotFoundError, version

import secretflow as sf
from secretflow.component.core import get_comp_list_def


def main() -> int:
    try:
        dist_version = version("secretflow")
    except PackageNotFoundError:
        dist_version = "not-installed"

    comp_list = get_comp_list_def()

    print(f"secretflow-distribution: {dist_version}")
    print(f"secretflow-module: {sf.__file__}")
    print(f"secretflow-version: {sf.__version__}")
    print(f"component-count: {len(comp_list.comps)}")
    print(f"component-version: {comp_list.version}")
    print(f"PYU-class: {sf.PYU}")
    print(f"SPU-class: {sf.SPU}")
    print(f"TEEU-class: {sf.TEEU}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only RoboTwin workspace prerequisite checker.

Run this from or against a RoboTwin workspace to check common setup blockers.
It does not import the RoboTwin `envs` package, download assets, initialize
submodules, or mutate files.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


MODULES = ["numpy", "torch", "sapien", "mplib", "open3d", "gymnasium", "transforms3d", "cv2", "h5py", "yaml", "rich"]
ASSET_PATHS = [
    "assets/objects/objaverse/list.json",
    "assets/objects/same.json",
    "assets/embodiments",
]
SUBMODULE_PATHS = [
    "XPolicyLab/setup_policy_server.py",
    "XPolicyLab/policy",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    root = args.workspace.resolve()
    ok = True

    print(f"workspace={root}")
    for rel in ["README.md", "envs", "env_cfg", "scripts", "description"]:
        exists = (root / rel).exists()
        print(f"path {rel}: {'ok' if exists else 'missing'}")
        ok = ok and exists

    for module in MODULES:
        spec = importlib.util.find_spec(module)
        print(f"module {module}: {'ok' if spec else 'missing'}")
        ok = ok and bool(spec)

    for rel in ASSET_PATHS:
        exists = (root / rel).exists()
        print(f"asset {rel}: {'ok' if exists else 'missing'}")
        ok = ok and exists

    for rel in SUBMODULE_PATHS:
        exists = (root / rel).exists()
        print(f"xpolicylab {rel}: {'ok' if exists else 'missing'}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

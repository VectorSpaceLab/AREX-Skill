#!/usr/bin/env python3
"""Validate a small typed cuRobo scene without opening a viewer."""
from __future__ import annotations

import argparse

from curobo.scene import Cuboid, Scene, Sphere


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a cuRobo scene smoke fixture")
    parser.parse_args()
    scene = Scene(
        cuboid=[Cuboid(name="table", dims=[1.0, 1.0, 0.1], pose=[0.0, 0.0, -0.05, 1, 0, 0, 0])],
        sphere=[Sphere(name="tool_clearance", radius=0.05, pose=[0.3, 0.0, 0.4, 1, 0, 0, 0])],
    )
    assert len(scene.cuboid) == 1 and len(scene.sphere) == 1
    print({"cuboids": len(scene.cuboid), "spheres": len(scene.sphere)})


if __name__ == "__main__":
    main()

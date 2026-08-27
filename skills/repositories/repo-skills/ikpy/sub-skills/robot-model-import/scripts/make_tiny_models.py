#!/usr/bin/env python3
"""Create small self-contained URDF/MJCF fixtures for IKPy smoke checks.

The default is a newly-created temporary directory.  Use --output-dir to put
fixtures in a caller-owned temporary directory.  Only the three named files
are written; no meshes, renders, or simulator assets are required.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


URDF_TEXT = """<robot name="tiny_arm">
  <link name="base_link"/>
  <link name="slider_link"/>
  <link name="wrist_link"/>
  <link name="tip_link"/>
  <joint name="slide_joint" type="prismatic">
    <parent link="base_link"/>
    <child link="slider_link"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <axis xyz="1 0 0"/>
    <limit lower="-0.2" upper="0.2"/>
  </joint>
  <joint name="wrist_joint" type="revolute">
    <parent link="slider_link"/>
    <child link="wrist_link"/>
    <origin xyz="0 0 0.2" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-1.57079632679" upper="1.57079632679"/>
  </joint>
  <joint name="tip_fixed" type="fixed">
    <parent link="wrist_link"/>
    <child link="tip_link"/>
    <origin xyz="0.2 0 0" rpy="0 0 0"/>
  </joint>
</robot>
"""

MJCF_TEXT = """<mujoco model="tiny_arm">
  <compiler angle="degree" eulerseq="zyx"/>
  <default class="hinge_defaults">
    <joint axis="0 0 1"/>
  </default>
  <worldbody>
    <body name="base" pos="0 0 0">
      <body name="slider" pos="0 0 0.1">
        <joint name="slide_joint" type="slide" axis="1 0 0" range="-0.2 0.2"/>
        <body name="wrist" pos="0.2 0 0" euler="0 0 90" childclass="hinge_defaults">
          <joint name="wrist_joint" type="hinge" range="-90 90"/>
          <body name="tip" pos="0.2 0 0"/>
        </body>
      </body>
    </body>
  </worldbody>
</mujoco>
"""


def write_fixture_set(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    urdf_path = output_dir / "tiny.urdf"
    mjcf_path = output_dir / "tiny.xml"
    json_path = output_dir / "tiny.json"

    urdf_path.write_text(URDF_TEXT, encoding="utf-8")
    mjcf_path.write_text(MJCF_TEXT, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "urdf_file": urdf_path.name,
                "elements": [
                    "base_link",
                    "slide_joint",
                    "slider_link",
                    "wrist_joint",
                    "wrist_link",
                    "tip_fixed",
                    "tip_link",
                ],
                "active_links_mask": [False, True, True, False],
                "last_link_vector": "",
                "name": "tiny_arm",
                "version": "v1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"urdf": urdf_path, "mjcf": mjcf_path, "json": json_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="directory for tiny.urdf, tiny.xml, and tiny.json; default is a new temporary directory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="ikpy-models-"))
    files = write_fixture_set(output_dir)
    print(f"fixture_dir: {output_dir.resolve()}")
    for kind, path in files.items():
        print(f"{kind}: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

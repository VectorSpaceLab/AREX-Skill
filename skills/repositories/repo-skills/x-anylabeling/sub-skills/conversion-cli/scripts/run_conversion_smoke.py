#!/usr/bin/env python3
"""Run a tiny xanylabeling conversion smoke test.

The script creates or reuses a deterministic YOLO detection fixture, runs:

  xanylabeling convert --task yolo2xlabel --mode detect ...

and asserts the generated XLABEL JSON contains exactly one rectangle shape for
class "box". It exits nonzero on command failure or assertion failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from create_conversion_fixture import create_fixture
except ImportError:  # pragma: no cover - supports direct execution from elsewhere
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from create_conversion_fixture import create_fixture


def _resolve_cli(explicit: str | None) -> str:
    if explicit:
        return explicit
    found = shutil.which("xanylabeling")
    if found:
        return found
    raise FileNotFoundError(
        "Could not find 'xanylabeling' on PATH. Pass --xanylabeling-bin or "
        "activate an environment where x-anylabeling-cvhub is installed."
    )


def _assert_rectangle(json_path: Path) -> None:
    if not json_path.exists():
        raise AssertionError(f"Expected output JSON was not created: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("imageWidth") == 10, data.get("imageWidth")
    assert data.get("imageHeight") == 10, data.get("imageHeight")
    assert data.get("imagePath") == "tiny.png", data.get("imagePath")

    shapes = data.get("shapes")
    if not isinstance(shapes, list):
        raise AssertionError("XLABEL 'shapes' is not a list")
    if len(shapes) != 1:
        raise AssertionError(f"Expected exactly one shape, found {len(shapes)}")

    shape = shapes[0]
    if shape.get("label") != "box":
        raise AssertionError(f"Expected label 'box', found {shape.get('label')!r}")
    if shape.get("shape_type") != "rectangle":
        raise AssertionError(
            f"Expected shape_type 'rectangle', found {shape.get('shape_type')!r}"
        )
    points = shape.get("points")
    if not isinstance(points, list) or len(points) != 4:
        raise AssertionError(f"Expected four rectangle points, found {points!r}")

    expected = [[3.0, 3.0], [7.0, 3.0], [7.0, 7.0], [3.0, 7.0]]
    for actual, exp in zip(points, expected):
        if len(actual) != 2:
            raise AssertionError(f"Invalid point: {actual!r}")
        if abs(float(actual[0]) - exp[0]) > 1e-6 or abs(float(actual[1]) - exp[1]) > 1e-6:
            raise AssertionError(f"Unexpected rectangle point {actual!r}; expected {exp!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir",
        type=Path,
        required=True,
        help="Fixture and output directory for the smoke test.",
    )
    parser.add_argument(
        "--xanylabeling-bin",
        help="Optional path to the xanylabeling executable. Defaults to PATH lookup.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not rewrite fixture files before running conversion.",
    )
    args = parser.parse_args()

    cli = _resolve_cli(args.xanylabeling_bin)
    paths = create_fixture(args.work_dir, overwrite=not args.keep_existing)
    expected_json = paths["expected_json"]
    if expected_json.exists():
        expected_json.unlink()

    cmd = [
        cli,
        "convert",
        "--task",
        "yolo2xlabel",
        "--mode",
        "detect",
        "--images",
        str(paths["images"]),
        "--labels",
        str(paths["labels"]),
        "--output",
        str(paths["output"]),
        "--classes",
        str(paths["classes"]),
    ]
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)

    _assert_rectangle(expected_json)
    print(f"Smoke conversion passed: {expected_json}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"conversion smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

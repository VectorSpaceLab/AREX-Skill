#!/usr/bin/env python3
"""Run a small cross-cutting LayoutParser smoke check.

The script stays fully local: it creates synthetic layout objects, exercises
serialization round-trips, and renders simple box/text overlays on a synthetic
image.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image

import layoutparser as lp


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def run_smoke() -> dict:
    layout = lp.Layout(
        [
            lp.Interval(2, 12, axis="x", canvas_height=64, canvas_width=64),
            lp.Rectangle(5, 5, 24, 20),
            lp.TextBlock(lp.Rectangle(8, 34, 26, 48), text="Demo", id=7, type="text"),
        ],
        page_data={"width": 64, "height": 64},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        json_path = tmpdir / "layout.json"
        csv_path = tmpdir / "layout.csv"
        json_path.write_text(json.dumps(layout.to_dict(), indent=2, default=_json_default))
        layout.to_dataframe().to_csv(csv_path, index=False)

        loaded_json = lp.load_json(str(json_path))
        loaded_csv = lp.load_csv(str(csv_path))
        loaded_csv.page_data = layout.page_data

    canvas = Image.new("RGB", (64, 64), "white")
    drawn_box = lp.draw_box(canvas, layout, box_width=2, box_alpha=0.15)
    drawn_text = lp.draw_text(canvas, lp.Layout([layout[-1]]), with_box_on_text=True)

    assert loaded_json == layout
    assert loaded_csv == layout
    assert drawn_box.size == (64, 64)
    assert drawn_text.size[0] >= 64

    return {
        "layout_version": lp.__version__,
        "roundtrip_json": True,
        "roundtrip_csv": True,
        "draw_box_mode": drawn_box.mode,
        "draw_text_mode": drawn_text.mode,
        "block_count": len(layout),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"layoutparser {result['layout_version']} smoke passed")
        for key in ["roundtrip_json", "roundtrip_csv", "draw_box_mode", "draw_text_mode", "block_count"]:
            print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

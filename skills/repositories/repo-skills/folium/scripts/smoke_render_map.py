#!/usr/bin/env python3
"""Render a tiny Folium map to HTML.

This is a safe smoke check for the core map and layer-composition workflow.
It does not require network downloads while running; it only writes HTML.
Use --open if you want to launch the result in a browser.
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

import folium


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a tiny Folium map to HTML.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default="folium-core-map.html",
        help="Output HTML file path.",
    )
    parser.add_argument(
        "--tiles",
        default="CartoDB Positron",
        help="Tile layer name, custom URL, or 'none' for no base tiles.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the written HTML file in the default browser.",
    )
    return parser.parse_args(argv)


def normalize_tiles(raw: str):
    if raw.strip().lower() == "none":
        return None
    return raw


def build_map(tiles) -> folium.Map:
    m = folium.Map(location=[37.78, -122.42], zoom_start=11, tiles=tiles)

    folium.map.CustomPane("routes", z_index=650).add_to(m)

    sample = folium.FeatureGroup(name="Sample places")
    sample.add_child(
        folium.Marker(
            [37.7749, -122.4194],
            tooltip="San Francisco",
            popup=folium.Popup("San Francisco"),
        )
    )
    sample.add_child(
        folium.Marker(
            [37.8044, -122.2711],
            tooltip="Oakland",
            popup="Oakland",
        )
    )
    sample.add_to(m)

    folium.PolyLine(
        [[37.7749, -122.4194], [37.8044, -122.2711]],
        color="purple",
        weight=4,
        tooltip="Route",
        pane="routes",
    ).add_to(m)

    folium.Rectangle(
        bounds=[[37.70, -122.55], [37.85, -122.30]],
        color="green",
        fill=False,
        pane="routes",
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds(sample.get_bounds())
    return m


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    gallery = build_map(normalize_tiles(args.tiles))
    gallery.save(str(output))
    print(f"Wrote {output}")

    if args.open:
        webbrowser.open(output.resolve().as_uri())
        print("Opened the map in your browser.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

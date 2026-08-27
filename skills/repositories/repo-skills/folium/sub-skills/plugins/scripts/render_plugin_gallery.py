#!/usr/bin/env python3
"""Render a tiny Folium plugin gallery to HTML.

The script uses only inline data so it can serve as a deterministic smoke check
for the plugin families covered by the sub-skill.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import folium
from folium.plugins import Draw, HeatMap, MarkerCluster, MiniMap


POINTS = [
    (37.7749, -122.4194, 0.9, "San Francisco"),
    (37.8044, -122.2711, 0.7, "Oakland"),
    (37.3382, -121.8863, 0.5, "San Jose"),
]


def build_map() -> folium.Map:
    """Build a tiny map that exercises the chosen plugin classes."""

    m = folium.Map(location=[37.65, -122.1], zoom_start=9)

    locations = [(lat, lon) for lat, lon, _, _ in POINTS]
    popups = [label for _, _, _, label in POINTS]
    heat_data = [(lat, lon, weight) for lat, lon, weight, _ in POINTS]

    MarkerCluster(locations=locations, popups=popups, name="Clustered points").add_to(m)
    HeatMap(heat_data, name="Heat density", radius=20, blur=12).add_to(m)
    Draw(export=True, filename="plugin-gallery.geojson").add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a tiny Folium plugin gallery to HTML."
    )
    parser.add_argument(
        "--output",
        default="plugin-gallery.html",
        help="Output HTML file path (default: plugin-gallery.html).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    gallery = build_map()
    gallery.save(str(output))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

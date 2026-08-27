#!/usr/bin/env python3
"""Render a tiny Folium GeoJSON choropleth demo.

The default data are embedded and offline-safe. Optional --geojson and --csv
arguments can point to local files or inline JSON/CSV content. The script
validates the join key, property fields, duplicate ids, and bins before
rendering HTML.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional, Union

DEFAULT_GEOJSON: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "A",
            "properties": {"name": "Alpha", "category": "north"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-101.0, 40.0],
                    [-100.0, 40.0],
                    [-100.0, 41.0],
                    [-101.0, 41.0],
                    [-101.0, 40.0],
                ]],
            },
        },
        {
            "type": "Feature",
            "id": "B",
            "properties": {"name": "Beta", "category": "south"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-100.0, 39.0],
                    [-99.0, 39.0],
                    [-99.0, 40.0],
                    [-100.0, 40.0],
                    [-100.0, 39.0],
                ]],
            },
        },
    ],
}

DEFAULT_ROWS = [
    {"id": "A", "value": 12},
    {"id": "B", "value": 27},
]


def parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_bins(raw: str) -> Union[int, list[float]]:
    raw = raw.strip()
    if "," in raw:
        try:
            bins = [float(piece.strip()) for piece in raw.split(",") if piece.strip()]
        except ValueError as exc:
            raise ValueError(
                f"Could not parse --bins value {raw!r} as a comma-separated list of numbers."
            ) from exc
        if len(bins) < 2:
            raise ValueError("--bins needs at least two edges when given as a list.")
        if any(right <= left for left, right in zip(bins, bins[1:])):
            raise ValueError("--bins edges must be strictly increasing.")
        return bins
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse --bins value {raw!r} as an integer or comma-separated list."
        ) from exc


def load_geojson(raw: Optional[str]) -> dict[str, Any]:
    if raw is None:
        return deepcopy(DEFAULT_GEOJSON)

    path = Path(raw)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"GeoJSON file {path} is not valid JSON: {exc}") from exc

    stripped = raw.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--geojson value is not valid JSON: {exc}") from exc

    raise ValueError(
        f"--geojson must be an existing local file path or inline JSON, got {raw!r}"
    )


def load_dataframe(raw: Optional[str]):
    import pandas as pd

    if raw is None:
        return pd.DataFrame(DEFAULT_ROWS)

    path = Path(raw)
    if not path.exists():
        raise ValueError(f"CSV file {path} does not exist.")

    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - pandas message is enough
        raise ValueError(f"Could not read CSV file {path}: {exc}") from exc


def resolve_path(node: Any, path: str) -> Any:
    current = node
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        else:
            return None
    return current


def validate_geojson(geojson: dict[str, Any], tooltip_fields: list[str], popup_fields: list[str], key_on: str) -> None:
    features = geojson.get("features")
    if geojson.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise ValueError("Expected a GeoJSON FeatureCollection with a 'features' list.")
    if not features:
        raise ValueError("GeoJSON FeatureCollection is empty.")

    first = features[0]
    props = first.get("properties") or {}
    if not isinstance(props, dict):
        raise ValueError("The first GeoJSON feature does not have a properties object.")

    requested = list(dict.fromkeys(tooltip_fields + popup_fields))
    missing_fields = [field for field in requested if field not in props]
    if missing_fields:
        available = ", ".join(sorted(props)) or "(none)"
        raise ValueError(
            "GeoJSON tooltip/popup field(s) not found in the first feature properties: "
            + ", ".join(missing_fields)
            + f". Available fields: {available}."
        )

    if key_on:
        path = key_on[8:] if key_on.startswith("feature.") else key_on
        if not any(resolve_path(feature, path) is not None for feature in features):
            raise ValueError(f"key_on {key_on!r} did not resolve in any GeoJSON feature.")


def validate_dataframe(df, key_column: str, value_column: str):
    import pandas as pd

    missing = [col for col in (key_column, value_column) if col not in df.columns]
    if missing:
        raise ValueError(
            "CSV data is missing required column(s): " + ", ".join(missing) + "."
        )

    if df[key_column].duplicated().any():
        duplicates = sorted(
            {str(value) for value in df.loc[df[key_column].duplicated(), key_column].tolist()}
        )
        raise ValueError(
            f"The key column {key_column!r} contains duplicates: {', '.join(duplicates)}."
        )

    converted = pd.to_numeric(df[value_column], errors="coerce")
    if converted.notna().sum() == 0:
        raise ValueError(f"The value column {value_column!r} did not contain any numeric data.")

    df = df.copy()
    df[value_column] = converted
    return df


def build_map(geojson: dict[str, Any], df, args):
    import folium

    if args.jenks and not isinstance(args.bins, int):
        raise ValueError("Jenks natural breaks requires an integer --bins value.")

    m = folium.Map(location=[0, 0], zoom_start=2, tiles="cartodbpositron")

    choropleth = folium.Choropleth(
        geo_data=geojson,
        data=df,
        columns=[args.key_column, args.value_column],
        key_on=args.key_on,
        bins=args.bins,
        fill_color=args.fill_color,
        nan_fill_color=args.nan_fill_color,
        nan_fill_opacity=args.nan_fill_opacity,
        legend_name=args.legend_name,
        name=args.layer_name,
        highlight=True,
        use_jenks=args.jenks,
    )
    choropleth.add_to(m)

    if args.tooltip_fields:
        choropleth.geojson.add_child(
            folium.GeoJsonTooltip(
                fields=args.tooltip_fields,
                aliases=args.tooltip_fields,
                labels=True,
                localize=True,
                class_name="foliumtooltip",
                sticky=True,
            )
        )

    if args.popup_fields:
        choropleth.geojson.add_child(
            folium.GeoJsonPopup(
                fields=args.popup_fields,
                aliases=args.popup_fields,
                labels=True,
                localize=True,
                class_name="foliumpopup",
            )
        )

    bounds = choropleth.geojson.get_bounds()
    if bounds != [[None, None], [None, None]]:
        m.fit_bounds(bounds)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def write_output(map_object, output: Optional[str]) -> Path:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        handle = tempfile.NamedTemporaryFile(
            suffix=".html",
            prefix="folium_geojson_choropleth_",
            delete=False,
        )
        handle.close()
        path = Path(handle.name)

    map_object.save(path.as_posix())
    return path


def parse_args(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(
        description="Render a tiny Folium GeoJSON choropleth demo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--geojson",
        help="Path to a local GeoJSON file or inline JSON text.",
    )
    parser.add_argument(
        "--csv",
        help="Path to a CSV file with a key column and a numeric value column.",
    )
    parser.add_argument(
        "--output",
        help="Write the rendered HTML map to this file. If omitted, a temporary file is used.",
    )
    parser.add_argument("--key-column", default="id", help="Table column used as the join key.")
    parser.add_argument("--value-column", default="value", help="Table column used as the numeric value.")
    parser.add_argument("--key-on", default="feature.id", help="GeoJSON lookup path used by Choropleth.")
    parser.add_argument("--bins", default="4", help="Integer bin count or comma-separated bin edges.")
    parser.add_argument("--fill-color", default="YlGn", help="ColorBrewer palette for the choropleth.")
    parser.add_argument("--legend-name", default="Values", help="Legend caption for the choropleth.")
    parser.add_argument("--nan-fill-color", default="lightgray", help="Fill color for missing values.")
    parser.add_argument("--nan-fill-opacity", type=float, default=0.35, help="Fill opacity for missing values.")
    parser.add_argument("--tooltip-fields", default="name,category", help="Comma-separated GeoJSON properties for the tooltip.")
    parser.add_argument("--popup-fields", default="name,category", help="Comma-separated GeoJSON properties for the popup.")
    parser.add_argument("--layer-name", default="GeoJSON choropleth", help="Layer name shown in Folium controls.")
    parser.add_argument("--jenks", action="store_true", help="Use Jenks natural breaks; requires jenkspy.")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        geojson = load_geojson(args.geojson)
        df = load_dataframe(args.csv)
        args.bins = parse_bins(args.bins)
        args.tooltip_fields = parse_csv_list(args.tooltip_fields)
        args.popup_fields = parse_csv_list(args.popup_fields)
        df = validate_dataframe(df, args.key_column, args.value_column)
        validate_geojson(geojson, args.tooltip_fields, args.popup_fields, args.key_on)

        if args.jenks:
            try:
                import jenkspy  # noqa: F401
            except ModuleNotFoundError as exc:
                raise ValueError(
                    "Jenks natural breaks requires the optional 'jenkspy' package."
                ) from exc

        map_object = build_map(geojson, df, args)
        output_path = write_output(map_object, args.output)

        print(f"Wrote {output_path}")
        print(
            "Rendered "
            f"{len(geojson['features'])} feature(s) with {len(df)} table row(s), "
            f"key_on={args.key_on!r}, bins={args.bins!r}."
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

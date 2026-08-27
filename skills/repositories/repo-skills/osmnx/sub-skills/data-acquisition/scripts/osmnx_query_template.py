#!/usr/bin/env python3
"""Generate a safe no-network OSMnx acquisition query plan.

The script never contacts Nominatim or Overpass. It prints a suggested OSMnx
call, the settings to apply first, and a short validation checklist.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

GRAPH_NETWORK_TYPES = ("all", "all_public", "bike", "drive", "drive_service", "walk")
GEOMETRIES = ("bbox", "point", "address", "place", "polygon", "xml")
WORKFLOWS = ("graph", "features", "geocode")


def parse_tag(spec: str) -> tuple[str, bool | str | list[str]]:
    """Parse KEY or KEY=VALUE into an OSMnx feature tag entry."""

    key, sep, raw_value = spec.partition("=")
    key = key.strip()
    if not key:
        raise ValueError("tag keys must not be empty")
    if not sep:
        return key, True

    value = raw_value.strip()
    if not value or value.lower() in {"true", "any", "*"}:
        return key, True
    if "," in value:
        values = [part.strip() for part in value.split(",") if part.strip()]
        if not values:
            raise ValueError(f"tag {spec!r} does not contain any values")
        return key, values
    return key, value


def parse_number_list(raw: list[str] | None, *, expected: int, name: str) -> list[float] | None:
    """Parse a fixed-length float list."""

    if raw is None:
        return None
    if len(raw) != expected:
        raise ValueError(f"{name} expects {expected} values")
    return [float(item) for item in raw]


def normalize_date(raw: str) -> str:
    """Normalize a historical Overpass date to UTC timestamp form."""

    value = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T00:00:00Z"
    if value.endswith("Z") or "T" in value:
        return value
    return f"{value}Z"


def build_overpass_settings(timeout: float, memory: int | None, historical_date: str | None) -> str:
    """Build the Overpass settings prefix string."""

    timeout_text = int(timeout) if float(timeout).is_integer() else timeout
    parts = ["[out:json]", f"[timeout:{timeout_text}]"]
    if memory is not None:
        parts.append(f"[maxsize:{memory}]")
    if historical_date:
        parts.append(f'[date:"{normalize_date(historical_date)}"]')
    return "".join(parts)


def parse_requests_kwargs(raw: str) -> Any:
    """Parse the raw requests kwargs display string when it is JSON-like."""

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def custom_filter_repr(filters: list[str]) -> str:
    if not filters:
        return "None"
    if len(filters) == 1:
        return repr(filters[0])
    return repr(filters)


def bbox_literal(values: list[float] | list[str] | None, fallback: list[str]) -> str:
    items = values or fallback
    return f"({items[0]}, {items[1]}, {items[2]}, {items[3]})"


def point_literal(values: list[float] | list[str] | None, fallback: list[str]) -> str:
    items = values or fallback
    return f"({items[0]}, {items[1]})"


def build_graph_call(args: argparse.Namespace) -> str:
    cf = custom_filter_repr(args.custom_filter)

    if args.geometry == "bbox":
        bbox = bbox_literal(args.bbox, ["<LEFT>", "<BOTTOM>", "<RIGHT>", "<TOP>"])
        return (
            f"ox.graph_from_bbox(bbox={bbox}, network_type={args.network_type!r}, "
            f"simplify={args.simplify}, retain_all={args.retain_all}, "
            f"truncate_by_edge={args.truncate_by_edge}, custom_filter={cf})"
        )

    if args.geometry == "point":
        point = point_literal(args.point, ["<LAT>", "<LON>"])
        return (
            f"ox.graph_from_point(center_point={point}, dist={args.dist}, dist_type={args.dist_type!r}, "
            f"network_type={args.network_type!r}, simplify={args.simplify}, retain_all={args.retain_all}, "
            f"truncate_by_edge={args.truncate_by_edge}, custom_filter={cf})"
        )

    if args.geometry == "address":
        query = args.query or "<QUERY>"
        return (
            f"ox.graph_from_address(address={query!r}, dist={args.dist}, dist_type={args.dist_type!r}, "
            f"network_type={args.network_type!r}, simplify={args.simplify}, retain_all={args.retain_all}, "
            f"truncate_by_edge={args.truncate_by_edge}, custom_filter={cf})"
        )

    if args.geometry == "place":
        query = args.query or "<QUERY>"
        pieces = [
            f"query={query!r}",
            f"network_type={args.network_type!r}",
            f"simplify={args.simplify}",
            f"retain_all={args.retain_all}",
            f"truncate_by_edge={args.truncate_by_edge}",
            f"custom_filter={cf}",
        ]
        if args.which_result is not None:
            pieces.append(f"which_result={args.which_result}")
        return f"ox.graph_from_place({', '.join(pieces)})"

    if args.geometry == "polygon":
        return (
            f"ox.graph_from_polygon(polygon=<POLYGON>, network_type={args.network_type!r}, "
            f"simplify={args.simplify}, retain_all={args.retain_all}, "
            f"truncate_by_edge={args.truncate_by_edge}, custom_filter={cf})"
        )

    filepath = f"Path({(args.xml or '<FILEPATH>')!r})"
    return (
        f"ox.graph_from_xml(filepath={filepath}, bidirectional={args.bidirectional}, "
        f"simplify={args.simplify}, retain_all={args.retain_all}, encoding={args.encoding!r})"
    )


def build_features_call(args: argparse.Namespace, tags: dict[str, bool | str | list[str]]) -> str:
    tags_repr = repr(tags)

    if args.geometry == "bbox":
        bbox = bbox_literal(args.bbox, ["<LEFT>", "<BOTTOM>", "<RIGHT>", "<TOP>"])
        return f"ox.features_from_bbox(bbox={bbox}, tags={tags_repr})"

    if args.geometry == "point":
        point = point_literal(args.point, ["<LAT>", "<LON>"])
        return f"ox.features_from_point(center_point={point}, tags={tags_repr}, dist={args.dist})"

    if args.geometry == "address":
        query = args.query or "<QUERY>"
        return f"ox.features_from_address(address={query!r}, tags={tags_repr}, dist={args.dist})"

    if args.geometry == "place":
        query = args.query or "<QUERY>"
        pieces = [f"query={query!r}", f"tags={tags_repr}"]
        if args.which_result is not None:
            pieces.append(f"which_result={args.which_result}")
        return f"ox.features_from_place({', '.join(pieces)})"

    if args.geometry == "polygon":
        return f"ox.features_from_polygon(polygon=<POLYGON>, tags={tags_repr})"

    pieces = [f"filepath=Path({(args.xml or '<FILEPATH>')!r})"]
    if tags:
        pieces.append(f"tags={tags_repr}")
    pieces.append(f"encoding={args.encoding!r}")
    return f"ox.features_from_xml({', '.join(pieces)})"


def build_geocode_call(args: argparse.Namespace) -> str:
    query = args.query or "<QUERY>"
    if args.by_osmid or args.geocode_output == "gdf":
        pieces = [f"query={query!r}"]
        if args.which_result is not None:
            pieces.append(f"which_result={args.which_result}")
        if args.by_osmid:
            pieces.append("by_osmid=True")
        return f"ox.geocode_to_gdf({', '.join(pieces)})"
    return f"ox.geocode({query!r})"


def build_settings(args: argparse.Namespace, overpass_settings: str) -> dict[str, Any]:
    return {
        "use_cache": args.use_cache,
        "cache_folder": args.cache_folder,
        "cache_only_mode": args.cache_only_mode,
        "requests_timeout": args.requests_timeout,
        "requests_kwargs": parse_requests_kwargs(args.requests_kwargs),
        "http_user_agent": args.http_user_agent,
        "http_referer": args.http_referer,
        "http_accept_language": args.http_accept_language,
        "nominatim_url": args.nominatim_url,
        "nominatim_key": args.nominatim_key,
        "overpass_url": args.overpass_url,
        "overpass_rate_limit": args.overpass_rate_limit,
        "overpass_memory": args.overpass_memory,
        "overpass_settings": overpass_settings,
        "default_crs": "epsg:4326",
        "default_access": args.default_access,
        "bidirectional_network_types": ["walk"],
        "max_query_area_size": args.max_query_area_size,
        "useful_tags_node": ["highway", "junction", "railway", "ref"],
        "useful_tags_way": [
            "access",
            "area",
            "bridge",
            "est_width",
            "highway",
            "junction",
            "landuse",
            "lanes",
            "maxspeed",
            "name",
            "oneway",
            "ref",
            "service",
            "tunnel",
            "width",
        ],
    }


def build_notes(args: argparse.Namespace, tags: dict[str, bool | str | list[str]]) -> list[str]:
    notes = ["No network request will be made by this script."]
    if args.workflow == "graph" and args.geometry == "point" and args.dist_type == "network":
        notes.append(
            "`dist_type=network` uses nearest-node search after the bbox graph is built; install the nearest-neighbor optional dependency set if that import path is unavailable.",
        )
    if args.workflow == "features":
        notes.append("Feature tags are unioned: a match on any requested tag branch is enough.")
    if args.workflow == "graph" and args.custom_filter:
        notes.append("A single custom-filter string intersects conditions; multiple custom-filter arguments are treated as alternatives.")
    if args.cache_only_mode:
        notes.append("`cache_only_mode=True` stops after caching the Overpass response and raises `CacheOnlyInterruptError`.")
    if args.historical_date:
        notes.append("Historical Overpass queries encode the date inside `overpass_settings`.")
    if args.geometry == "xml" and args.query:
        notes.append("For XML plans, the free-form query text is kept as a note rather than sent to a live API.")
    if tags:
        notes.append("For features workflows, `True` means any value for the tag key, a string means one exact value, and a list means any listed value.")
    return notes


def build_validation(args: argparse.Namespace) -> list[str]:
    items = [
        "Confirm bbox order is `(left, bottom, right, top)` and point order is `(lat, lon)`.",
        "Confirm the geometry is in `EPSG:4326` before querying.",
        "Confirm `which_result` is 1-based and aligns with any list of queries.",
        "Confirm the query family matches the needed output: graph, GeoDataFrame, or geocode point.",
    ]
    if args.workflow == "geocode" and args.by_osmid:
        items.append("Confirm the OSM ID uses the `N`, `W`, or `R` prefix expected by Nominatim lookup.")
    if args.workflow == "features":
        items.append("Confirm the tags are broad enough to match at least one feature branch.")
    if args.geometry == "xml":
        items.append("Confirm the XML file is raw downloaded OSM XML, not a saved OSMnx graph.")
    if args.workflow == "graph" and args.geometry in {"address", "place"}:
        items.append("Confirm the geocoded result is a Polygon or MultiPolygon before querying Overpass.")
    if args.workflow == "graph" and args.geometry == "point" and args.dist_type == "network":
        items.append("Confirm the nearest-neighbor optional dependency set is available for network-distance truncation.")
    return items


def build_text(plan: dict[str, Any]) -> str:
    lines = ["OSMnx no-network query plan", ""]
    lines.append(f"Workflow: {plan['workflow']}")
    lines.append(f"Geometry: {plan['geometry']}")
    lines.append(f"Suggested function: {plan['function']}")
    lines.append("")
    lines.append("Suggested call:")
    lines.append(f"  {plan['call']}")
    lines.append("")
    lines.append("Settings:")
    for key, value in plan["settings"].items():
        lines.append(f"  - {key} = {value!r}")
    lines.append("")
    lines.append("Notes:")
    for note in plan["notes"]:
        lines.append(f"  - {note}")
    lines.append("")
    if plan["tags"]:
        lines.append("Tags:")
        lines.append("  " + json.dumps(plan["tags"], indent=2, sort_keys=True).replace("\n", "\n  "))
        lines.append("")
    if plan["custom_filter"]:
        lines.append("Custom filters:")
        lines.append(f"  {json.dumps(plan['custom_filter'], indent=2)}")
        lines.append("")
    lines.append("Validation checklist:")
    for item in plan["validation"]:
        lines.append(f"  - {item}")
    return "\n".join(lines)


def build_python(plan: dict[str, Any]) -> str:
    lines = ["import osmnx as ox", "from pathlib import Path", ""]
    for key, value in plan["settings"].items():
        if key == "requests_kwargs":
            if value in ({}, "{}"):  # safe default remains executable
                lines.append("ox.settings.requests_kwargs = {}")
            else:
                lines.append(f"# ox.settings.{key} = {value}")
        else:
            lines.append(f"ox.settings.{key} = {value!r}")
    lines.append("")
    if plan["geometry"] == "xml" and plan["workflow"] == "graph":
        lines.append("# The XML path should point to raw downloaded OSM XML.")
    if plan["geometry"] == "xml" and plan["workflow"] == "features":
        lines.append("# `polygon` and `tags` are optional for local XML parsing.")
    lines.append(f"result = {plan['call']}")
    return "\n".join(lines)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a safe no-network OSMnx acquisition query plan.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workflow", choices=WORKFLOWS, required=True, help="Which OSMnx acquisition family to plan.")
    parser.add_argument("--geometry", choices=GEOMETRIES, help="Which geometry or source type to plan.")
    parser.add_argument("--geocode-output", choices=("point", "gdf"), default="point", help="Geocode output shape for workflow=geocode.")
    parser.add_argument("--query", help="Text query for geocode, address, or place plans; may also be used as a note for polygon/XML plans.")
    parser.add_argument("--bbox", nargs=4, metavar=("LEFT", "BOTTOM", "RIGHT", "TOP"), help="Bounding box coordinates.")
    parser.add_argument("--point", nargs=2, metavar=("LAT", "LON"), help="Point coordinates.")
    parser.add_argument("--xml", help="Path to a local OSM XML file.")
    parser.add_argument("--dist", type=float, default=500.0, help="Distance in meters for point/address plans.")
    parser.add_argument("--dist-type", choices=("bbox", "network"), default="bbox", help="How to truncate point/address graph queries.")
    parser.add_argument("--network-type", choices=GRAPH_NETWORK_TYPES, default="all", help="Built-in street-network filter preset.")
    parser.add_argument("--simplify", action=argparse.BooleanOptionalAction, default=True, help="Simplify graphs after acquisition.")
    parser.add_argument("--retain-all", action="store_true", help="Keep all graph components instead of only the largest one.")
    parser.add_argument("--truncate-by-edge", action="store_true", help="Keep nodes outside the query geometry if they connect to it.")
    parser.add_argument("--bidirectional", action="store_true", help="Force bidirectional edges when reading local XML.")
    parser.add_argument("--which-result", type=int, help="1-based geocoder result to use for ambiguous place queries.")
    parser.add_argument("--by-osmid", action="store_true", help="Treat a geocode query as an OSM ID lookup.")
    parser.add_argument("--tag", action="append", default=[], metavar="KEY[=VALUE]", help="Feature tag branch. Repeat for multiple branches.")
    parser.add_argument("--custom-filter", action="append", default=[], help="Graph custom filter branch. Repeat to generate a list-of-filters plan.")
    parser.add_argument("--historical-date", help="Historical Overpass date, e.g. 2019-10-28 or 2019-10-28T00:00:00Z.")
    parser.add_argument("--use-cache", action=argparse.BooleanOptionalAction, default=True, help="Use the local HTTP cache.")
    parser.add_argument("--cache-folder", default="./cache", help="Where to store cache files.")
    parser.add_argument("--cache-only-mode", action=argparse.BooleanOptionalAction, default=False, help="Save Overpass responses and stop before graph/feature assembly.")
    parser.add_argument("--requests-timeout", type=float, default=180.0, help="HTTP and Overpass timeout in seconds.")
    parser.add_argument("--requests-kwargs", default="{}", help="Opaque `requests` kwargs string to display in the plan.")
    parser.add_argument("--http-user-agent", default='OSMnx Python package (https://github.com/gboeing/osmnx)', help="HTTP User-Agent header.")
    parser.add_argument("--http-referer", default='OSMnx Python package (https://github.com/gboeing/osmnx)', help="HTTP Referer header.")
    parser.add_argument("--http-accept-language", default="en", help="HTTP Accept-Language header.")
    parser.add_argument("--nominatim-url", default="https://nominatim.openstreetmap.org/", help="Nominatim base URL.")
    parser.add_argument("--nominatim-key", default=None, help="Optional Nominatim API key.")
    parser.add_argument("--overpass-url", default="https://overpass-api.de/api", help="Overpass base URL.")
    parser.add_argument("--overpass-rate-limit", action=argparse.BooleanOptionalAction, default=True, help="Respect public Overpass slot waiting.")
    parser.add_argument("--overpass-memory", type=int, default=None, help="Overpass maxsize in bytes.")
    parser.add_argument("--default-access", default='["access"!~"private"]', help="Default built-in access filter for graph presets.")
    parser.add_argument("--max-query-area-size", type=float, default=2_500_000_000.0, help="Maximum query area before OSMnx subdivides the polygon.")
    parser.add_argument("--encoding", default="utf-8", help="Encoding for local XML plans.")
    parser.add_argument("--format", choices=("text", "json", "python"), default="text", help="Output format for the plan.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.workflow != "geocode" and not args.geometry:
        parser.error("--geometry is required unless workflow=geocode")
    if args.workflow != "geocode" and args.geometry in {"address", "place"} and not args.query:
        parser.error("--query is required for address/place plans")
    if args.workflow != "geocode" and args.geometry == "bbox" and not args.bbox:
        parser.error("--bbox is required for bbox plans")
    if args.workflow != "geocode" and args.geometry == "point" and not args.point:
        parser.error("--point is required for point plans")
    if args.workflow != "geocode" and args.geometry == "xml" and not args.xml:
        parser.error("--xml is required for xml plans")
    if args.workflow == "features" and args.geometry != "xml" and not args.tag:
        parser.error("--tag is required for feature acquisition plans")
    if args.workflow == "geocode" and not args.query:
        parser.error("--query is required for geocode plans")
    if args.workflow != "geocode" and args.geometry not in GEOMETRIES:
        parser.error("--geometry must be one of the supported geometry types")

    if args.geometry == "bbox":
        args.bbox = parse_number_list(args.bbox, expected=4, name="--bbox")
    if args.geometry == "point":
        args.point = parse_number_list(args.point, expected=2, name="--point")

    tags: dict[str, bool | str | list[str]] = {}
    for spec in args.tag:
        key, value = parse_tag(spec)
        tags[key] = value

    overpass_settings = build_overpass_settings(args.requests_timeout, args.overpass_memory, args.historical_date)
    settings = build_settings(args, overpass_settings)

    if args.workflow == "geocode":
        call = build_geocode_call(args)
    elif args.workflow == "graph":
        call = build_graph_call(args)
    else:
        call = build_features_call(args, tags)

    plan = {
        "workflow": args.workflow,
        "geometry": args.geometry or "geocode",
        "function": call.split("(", 1)[0],
        "call": call,
        "settings": settings,
        "tags": tags,
        "custom_filter": args.custom_filter,
        "notes": build_notes(args, tags),
        "validation": build_validation(args),
    }

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True, default=str))
        return 0
    if args.format == "python":
        print(build_python(plan))
        return 0

    print(build_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

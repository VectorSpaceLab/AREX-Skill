#!/usr/bin/env python3
"""Build a BlenderGIS-style Overpass QL query without network access.

This helper adapts BlenderGIS' ``operators/io_import_osm.py::queryBuilder``
so agents can preflight bbox, tag, type, and output-format choices before using
``importgis.osm_query`` in Blender. It only prints a query string; it never
contacts Overpass and never reads Blender state.

Examples:
  python build_overpass_query.py --bbox=-74.02,40.70,-73.95,40.78 --tag building --type way --format xml
  python build_overpass_query.py --west -74.02 --south 40.70 --east -73.95 --north 40.78 --tag highway --type node
  python build_overpass_query.py -- -74.02,40.70,-73.95,40.78
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Iterable, List, Sequence

DEFAULT_TAGS = ["building", "highway"]
DEFAULT_TYPES = ["node", "way", "relation"]
ALLOWED_TYPES = {"node", "way", "relation", "rel"}
ALLOWED_FORMATS = {"json", "xml"}


@dataclass(frozen=True)
class BBox:
    """Bounding box accepted as west,south,east,north and emitted as south,west,north,east."""

    west: float
    south: float
    east: float
    north: float

    def to_latlon(self) -> Sequence[float]:
        """Return BlenderGIS BBOX.toLatlon() order: south, west, north, east."""

        return (self.south, self.west, self.north, self.east)


def _looks_like_bbox_token(token: str) -> bool:
    parts = token.split(",")
    if len(parts) != 4:
        return False
    try:
        [float(part.strip()) for part in parts]
    except ValueError:
        return False
    return True


def _preprocess_argv(argv: Sequence[str]) -> List[str]:
    """Allow a bare negative comma bbox token before argparse treats it as an option."""

    rewritten: List[str] = []
    converted = False
    for arg in argv:
        if not converted and _looks_like_bbox_token(arg):
            rewritten.append(f"--bbox={arg}")
            converted = True
        else:
            rewritten.append(arg)
    return rewritten


def _parse_bbox_string(value: str) -> BBox:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be west,south,east,north")
    try:
        west, south, east, north = [float(part.strip()) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox values must be numeric") from exc
    return _validate_bbox(BBox(west=west, south=south, east=east, north=north))


def _validate_bbox(bbox: BBox) -> BBox:
    if not (-180 <= bbox.west <= 180 and -180 <= bbox.east <= 180):
        raise argparse.ArgumentTypeError("west/east longitude must be between -180 and 180")
    if not (-90 <= bbox.south <= 90 and -90 <= bbox.north <= 90):
        raise argparse.ArgumentTypeError("south/north latitude must be between -90 and 90")
    if bbox.west >= bbox.east:
        raise argparse.ArgumentTypeError("west must be smaller than east; antimeridian-spanning bboxes are not supported")
    if bbox.south >= bbox.north:
        raise argparse.ArgumentTypeError("south must be smaller than north")
    return bbox


def _format_float(value: float) -> str:
    text = f"{value:.12g}"
    if text == "-0":
        return "0"
    return text


def build_query(bbox: BBox, tags: Iterable[str] | None = None, types: Iterable[str] | None = None, fmt: str = "json") -> str:
    """Return the same Overpass QL shape as BlenderGIS queryBuilder()."""

    if tags is None:
        tag_list = list(DEFAULT_TAGS)
    else:
        tag_list = [tag.strip() for tag in tags if tag.strip()]

    if types is None:
        type_list = list(DEFAULT_TYPES)
    else:
        type_list = [kind.strip().lower() for kind in types if kind.strip()]
        if not type_list:
            type_list = list(DEFAULT_TYPES)

    invalid_types = sorted(set(type_list) - ALLOWED_TYPES)
    if invalid_types:
        raise ValueError(f"unsupported OSM type(s): {', '.join(invalid_types)}")

    fmt = fmt.lower()
    if fmt not in ALLOWED_FORMATS:
        raise ValueError("format must be json or xml")

    bbox_str = ",".join(_format_float(value) for value in bbox.to_latlon())
    head = f"[out:{fmt}][bbox:{bbox_str}];"

    union = "("
    if "node" in type_list:
        if tag_list:
            union += ";".join(f"node[{tag}]" for tag in tag_list) + ";"
        else:
            union += "node;"

    if "way" in type_list:
        union += "(("
        if tag_list:
            union += ";".join(f"way[{tag}]" for tag in tag_list) + ";);"
        else:
            union += "way;);"
        union += ">;);"

    if "relation" in type_list or "rel" in type_list:
        union += "relation;"

    union += ")"
    return head + union + ";out;"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a BlenderGIS-style Overpass QL query from a bbox, tags, element types, and output format. No network is used.",
    )
    parser.add_argument(
        "bbox_positional",
        nargs="?",
        metavar="west,south,east,north",
        type=_parse_bbox_string,
        help="Bounding box as a comma-separated west,south,east,north string.",
    )
    parser.add_argument(
        "--bbox",
        dest="bbox_option",
        type=_parse_bbox_string,
        help="Bounding box as west,south,east,north. Useful when west is negative: --bbox=-74,40,-73,41.",
    )
    parser.add_argument("--west", type=float, help="Western longitude in EPSG:4326 degrees.")
    parser.add_argument("--south", type=float, help="Southern latitude in EPSG:4326 degrees.")
    parser.add_argument("--east", type=float, help="Eastern longitude in EPSG:4326 degrees.")
    parser.add_argument("--north", type=float, help="Northern latitude in EPSG:4326 degrees.")
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="OSM tag key or key=value filter. Repeat for multiple filters. Default: building and highway.",
    )
    parser.add_argument(
        "--type",
        action="append",
        dest="types",
        choices=sorted(ALLOWED_TYPES),
        help="OSM element type to include: node, way, relation, or rel. Repeat for multiple types. Default: node, way, relation.",
    )
    parser.add_argument(
        "--format",
        choices=sorted(ALLOWED_FORMATS),
        default="json",
        help="Overpass output format marker. BlenderGIS live query uses xml; source helper default is json.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(_preprocess_argv(argv))

    bbox_sources = [args.bbox_positional is not None, args.bbox_option is not None]
    has_component_bbox = all(value is not None for value in (args.west, args.south, args.east, args.north))
    any_component_bbox = any(value is not None for value in (args.west, args.south, args.east, args.north))

    if any_component_bbox and not has_component_bbox:
        parser.error("--west, --south, --east, and --north must be supplied together")

    bbox_sources.append(has_component_bbox)
    if sum(1 for item in bbox_sources if item) != 1:
        parser.error("provide exactly one bbox source: positional west,south,east,north, --bbox, or --west/--south/--east/--north")

    if args.bbox_option is not None:
        bbox = args.bbox_option
    elif args.bbox_positional is not None:
        bbox = args.bbox_positional
    else:
        try:
            bbox = _validate_bbox(BBox(args.west, args.south, args.east, args.north))
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))

    try:
        query = build_query(bbox=bbox, tags=args.tags, types=args.types, fmt=args.format)
    except ValueError as exc:
        parser.error(str(exc))

    print(query)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

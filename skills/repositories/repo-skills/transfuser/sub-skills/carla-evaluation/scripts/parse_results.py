#!/usr/bin/env python3
"""Safely aggregate TransFuser/CARLA result JSON files into CSV and SVG maps.

This is a self-contained adaptation of the repository's result_parser.py. It
uses only the Python standard library, never imports CARLA, and never launches
an external process. JSON and XML are read; output files are created only after
schema and coverage validation succeeds.
"""

from __future__ import print_function

import argparse
import base64
import csv
import json
import math
import re
from pathlib import Path
import statistics
import sys
import xml.etree.ElementTree as ET

INFRACTION_KEYS = (
    "collisions_layout", "collisions_pedestrian", "collisions_vehicle",
    "outside_route_lanes", "red_light", "route_dev", "route_timeout",
    "stop_infraction", "vehicle_blocked",
)
ROUTE_ID_RE = re.compile(r"(\d+)(?!.*\d)")
COORD_RE = re.compile(r"\(\s*x\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*,\s*y\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*,\s*z\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*\)")
DISTANCE_RE = re.compile(r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:m|meters?|metres?)", re.IGNORECASE)
LABEL_TO_INFRACTION = {
    "Collisions with pedestrians": "collisions_pedestrian",
    "Collisions with vehicles": "collisions_vehicle",
    "Collisions with layout": "collisions_layout",
    "Red lights infractions": "red_light",
    "Stop sign infractions": "stop_infraction",
    "Off-road infractions": "outside_route_lanes",
    "Route deviations": "route_dev",
    "Route timeouts": "route_timeout",
    "Agent blocked": "vehicle_blocked",
}

# Coordinates and scales are the values used by the repository parser for its
# Town01..Town06 map images. They are applied only when map output is requested.
REFERENCE_COORD = {
    "Town01": (-8.22, -8.187), "Town02": (-13.102, 0.148),
    "Town03": (-291.567, 320.126), "Town04": (-518.496, 398.342),
    "Town05": (-317.72, 217.554), "Town06": (-390.685, -160.232),
}
SCALE = {
    "Town01": (757 / 410, 636 / 345), "Town02": (434 / 214, 637 / 314),
    "Town03": (651 / 605, 637 / 590), "Town04": (708 / 940, 627 / 844),
    "Town05": (784 / 540, 632 / 436), "Town06": (920 / 1050, 522 / 570),
}
COLORS = {
    "collisions_layout": "#ff0000", "collisions_pedestrian": "#00ff00",
    "collisions_vehicle": "#0000ff", "outside_route_lanes": "#00ffff",
    "red_light": "#ffff00", "route_dev": "#ff00ff",
    "route_timeout": "#ffffff", "stop_infraction": "#777777",
    "vehicle_blocked": "#000000",
}


def fail(message):
    raise ValueError(message)


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        fail("{} must be a finite number".format(label))
    return float(value)


def route_numeric_id(route_id):
    match = ROUTE_ID_RE.search(str(route_id))
    if not match:
        fail("route id {!r} has no numeric suffix".format(route_id))
    return match.group(1)


def split_weather(weather_id):
    parts = re.findall(r"[A-Z][^A-Z]*", str(weather_id))
    if len(parts) < 2:
        return str(weather_id), "Unknown"
    return "".join(parts[:-1]), parts[-1]


def load_route_metadata(xml_path):
    try:
        root = ET.parse(str(xml_path)).getroot()
    except (OSError, ET.ParseError) as exc:
        fail("cannot parse route XML {}: {}".format(xml_path, exc))
    metadata = {}
    for route in root.iter("route"):
        route_id = route.attrib.get("id")
        town = route.attrib.get("town")
        if route_id is None or town is None:
            fail("route XML contains route without id/town")
        numeric = route_numeric_id(route_id)
        weather_node = route.find("weather")
        weather_id = weather_node.attrib.get("id", "Clear") if weather_node is not None else "Clear"
        weather, daytime = split_weather(weather_id)
        if numeric in metadata:
            fail("route XML has duplicate numeric route id {}".format(numeric))
        metadata[numeric] = {"xml_id": str(route_id), "town": town, "weather": weather, "daytime": daytime}
    if not metadata:
        fail("route XML contains no routes")
    return metadata


def result_files(inputs):
    paths = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file():
            if path.suffix.lower() == ".json":
                paths.append(path)
            else:
                fail("result input is not JSON: {}".format(path))
        elif path.is_dir():
            paths.extend(sorted(p for p in path.rglob("*.json") if p.is_file()))
        else:
            fail("result input does not exist: {}".format(path))
    unique = sorted(set(paths))
    if not unique:
        fail("no JSON result files found")
    return unique


def load_result(path):
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        fail("cannot parse result JSON {}: {}".format(path, exc))
    if not isinstance(data, dict):
        fail("result {} is not an object".format(path))
    checkpoint = data.get("_checkpoint")
    if not isinstance(checkpoint, dict):
        fail("result {} lacks _checkpoint object".format(path))
    records = checkpoint.get("records")
    if not isinstance(records, list):
        fail("result {} lacks _checkpoint.records array".format(path))
    labels, values = data.get("labels"), data.get("values")
    if not isinstance(labels, list) or not isinstance(values, list) or len(labels) != len(values):
        fail("result {} has invalid labels/values arrays".format(path))
    normalized_values = []
    for index, value in enumerate(values):
        try:
            normalized_values.append(finite(float(value), "{}.values[{}]".format(path, index)))
        except (TypeError, ValueError):
            fail("{}.values[{}] is not numeric: {!r}".format(path, index, value))
    normalized = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            fail("{}.records[{}] is not an object".format(path, index))
        for key in ("route_id", "status", "infractions", "scores", "meta"):
            if key not in record:
                fail("{}.records[{}] missing {}".format(path, index, key))
        scores = record["scores"]
        meta = record["meta"]
        infractions = record["infractions"]
        if not isinstance(scores, dict) or not isinstance(meta, dict) or not isinstance(infractions, dict):
            fail("{}.records[{}] has invalid scores/meta/infractions object".format(path, index))
        score_route = finite(scores.get("score_route"), "{}.records[{}].scores.score_route".format(path, index))
        score_composed = finite(scores.get("score_composed"), "{}.records[{}].scores.score_composed".format(path, index))
        route_length = finite(meta.get("route_length"), "{}.records[{}].meta.route_length".format(path, index))
        if route_length < 0 or score_route < 0:
            fail("{}.records[{}] has negative route length/completion".format(path, index))
        arrays = {}
        for key in INFRACTION_KEYS:
            value = infractions.get(key, [])
            if not isinstance(value, list):
                fail("{}.records[{}].infractions.{} must be an array".format(path, index, key))
            if not all(isinstance(item, str) for item in value):
                fail("{}.records[{}].infractions.{} must contain strings".format(path, index, key))
            arrays[key] = value
        duration_game = finite(meta.get("duration_game"), "{}.records[{}].meta.duration_game".format(path, index))
        normalized.append({
            "route_id": str(record["route_id"]), "status": str(record["status"]),
            "scores": {"score_route": score_route, "score_composed": score_composed},
            "route_length": route_length, "duration_game": duration_game, "infractions": arrays,
        })
    return {"path": path, "records": normalized, "labels": [str(x) for x in labels], "values": normalized_values}


def collect_records(files, route_metadata, failure_policy):
    records = []
    labels = None
    weighted_values = None
    for loaded in files:
        if labels is None:
            labels = loaded["labels"]
            weighted_values = [0.0] * len(labels)
        elif loaded["labels"] != labels:
            fail("result files use different labels; cannot aggregate safely")
        count = len(loaded["records"])
        for value_index, value in enumerate(loaded["values"]):
            weighted_values[value_index] += value * count
        for record in loaded["records"]:
            numeric = route_numeric_id(record["route_id"])
            if numeric not in route_metadata:
                fail("result route {} is absent from supplied route XML".format(record["route_id"]))
            if record["status"] in ("Failed", "Failed - Agent couldn't be set up", "Failed - Simulation crashed"):
                if failure_policy == "source":
                    fail("source failure policy rejects route {} status {!r}".format(record["route_id"], record["status"]))
            if failure_policy == "strict" and record["status"] != "Completed":
                fail("strict failure policy rejects route {} status {!r}".format(record["route_id"], record["status"]))
            enriched = dict(record)
            enriched["numeric_id"] = numeric
            enriched["route"] = enriched["route_id"]
            enriched.update(route_metadata[numeric])
            records.append(enriched)
    if not records:
        fail("no route records found")
    expected = set(route_metadata)
    counts = {route_id: 0 for route_id in expected}
    for record in records:
        counts[record["numeric_id"]] += 1
    missing = sorted(route_id for route_id, count in counts.items() if count == 0)
    uneven = sorted((route_id, count) for route_id, count in counts.items() if count and count != max(counts.values()))
    if missing:
        fail("missing route ids from result set: {}".format(", ".join(missing)))
    if uneven:
        fail("route result repetitions are uneven: {}".format(uneven))
    if len(records) % len(route_metadata) != 0:
        fail("record count {} is not a multiple of XML route count {}".format(len(records), len(route_metadata)))
    total_driven_km = sum((record["scores"]["score_route"] / 100.0) * record["route_length"] / 1000.0 for record in records)
    if total_driven_km <= 0:
        fail("aggregate driven distance is zero; per-kilometre metrics are undefined")
    return records, labels, [value / len(records) for value in weighted_values], total_driven_km


def parse_coords(description):
    match = COORD_RE.search(description)
    if not match:
        return None
    return tuple(float(match.group(i)) for i in (1, 2, 3))


def offroad_distance_km(description, route_label):
    match = DISTANCE_RE.search(description)
    if not match:
        # Some source descriptions say only percentage. Do not guess a length.
        fail("cannot extract off-route distance from {}: {!r}".format(route_label, description))
    distance = abs(float(match.group(1)))
    return distance / 1000.0


def stats(values):
    if not values:
        return 0.0, 0.0
    return statistics.mean(values), statistics.pstdev(values)


def record_infraction_count(record, key):
    if key == "outside_route_lanes":
        return sum(offroad_distance_km(text, "route {}".format(record["route_id"])) for text in record["infractions"][key])
    return float(len(record["infractions"][key]))


def grouped_rows(records, field):
    groups = {}
    for record in records:
        groups.setdefault(record[field], []).append(record)
    if field == "route":
        keys = sorted(groups, key=lambda value: int(route_numeric_id(value)))
    else:
        keys = sorted(groups, key=str)
    return [(key, groups[key]) for key in keys]


def aggregate_metrics(records, field=None):
    groups = [("all", records)] if field is None else grouped_rows(records, field)
    rows = []
    for key, items in groups:
        score = [x["scores"]["score_composed"] for x in items]
        completion = [x["scores"]["score_route"] for x in items]
        length = [x["route_length"] for x in items]
        duration = [x["duration_game"] for x in items]
        infractions = {infraction: [record_infraction_count(x, infraction) for x in items] for infraction in INFRACTION_KEYS}
        row = {"group": key, "score_mean": stats(score)[0], "score_std": stats(score)[1],
               "completion_mean": stats(completion)[0], "completion_std": stats(completion)[1],
               "duration_mean": stats(duration)[0], "duration_std": stats(duration)[1],
               "length_mean": stats(length)[0], "length_std": stats(length)[1]}
        for infraction, values in infractions.items():
            row[infraction + "_mean"] = stats(values)[0]
            row[infraction + "_std"] = stats(values)[1]
        if field == "route":
            row.update({"town": items[0]["town"], "weather": items[0]["weather"], "daytime": items[0]["daytime"]})
        rows.append(row)
    return rows


def global_values(records, labels, source_values, total_driven_km):
    totals = {key: sum(record_infraction_count(record, key) for record in records) for key in INFRACTION_KEYS}
    rates = {key: totals[key] / total_driven_km for key in INFRACTION_KEYS}
    rates["outside_route_lanes"] *= 100.0
    values = list(source_values)
    for index, label in enumerate(labels):
        if label in LABEL_TO_INFRACTION:
            values[index] = rates[LABEL_TO_INFRACTION[label]]
    return values, rates


def csv_rows(records, labels, source_values, total_driven_km):
    values, rates = global_values(records, labels, source_values, total_driven_km)
    rows = []
    for label, value in zip(labels, values):
        rows.append([label, value])
    rows.append([])
    infraction_headers = []
    for key in INFRACTION_KEYS:
        infraction_headers.extend([key + " mean", key + " std"])
    route_header = ["route", "town", "weather", "daytime", "score mean", "score std",
                    "completion mean", "completion std", "duration mean", "duration std",
                    "length mean", "length std"] + infraction_headers
    group_header = ["group", "score mean", "score std", "completion mean", "completion std",
                    "duration mean", "duration std", "length mean", "length std"] + infraction_headers
    for field in ("route", "town", "weather", "daytime", "status"):
        rows.append(route_header if field == "route" else group_header)
        for item in aggregate_metrics(records, field):
            values_row = [item["group"]]
            if field == "route":
                values_row.extend([item["town"], item["weather"], item["daytime"]])
            values_row.extend([item["score_mean"], item["score_std"], item["completion_mean"], item["completion_std"],
                                item["duration_mean"], item["duration_std"], item["length_mean"], item["length_std"]])
            for key in INFRACTION_KEYS:
                values_row.extend([item[key + "_mean"], item[key + "_std"]])
            rows.append(values_row)
        rows.append([])
    rows.append(["town", "weather", "daylight", "infraction type", "x", "y", "z"])
    for record in records:
        for key in INFRACTION_KEYS:
            for description in record["infractions"][key]:
                coords = parse_coords(description)
                if coords is not None:
                    rows.append([record["town"], record["weather"], record["daytime"], key] + list(coords))
    return rows, rates


def png_size(path):
    # PNG IHDR is fixed at bytes 16..23; checking signature and dimensions is
    # enough for embedding without requiring Pillow.
    with path.open("rb") as handle:
        blob = handle.read(24)
    if len(blob) < 24 or blob[:8] != b"\x89PNG\r\n\x1a\n":
        fail("{} is not a valid PNG header".format(path))
    width = int.from_bytes(blob[16:20], "big")
    height = int.from_bytes(blob[20:24], "big")
    if width <= 0 or height <= 0:
        fail("{} has invalid PNG dimensions".format(path))
    return width, height


def pixel(coord, town):
    x, y, _ = coord
    ref = REFERENCE_COORD[town]
    scale = SCALE[town]
    px = int((x - ref[0]) * scale[0])
    py = int(-(y - ref[1]) * scale[1])
    if town in ("Town03", "Town04"):
        py = int(-(-y - ref[1]) * scale[1])
    if town in ("Town01", "Town02", "Town06"):
        px, py = abs(px), abs(py)
    return px, py


def write_svg_maps(records, maps_dir, output_dir, overwrite):
    maps_dir = Path(maps_dir).expanduser().resolve()
    output_dir = Path(output_dir)
    warnings = []
    used_towns = sorted(set(record["town"] for record in records))
    for town in used_towns:
        if town not in REFERENCE_COORD:
            warnings.append("no coordinate transform for {}".format(town))
            continue
        image = maps_dir / (town + ".png")
        if not image.is_file():
            warnings.append("missing map image {}".format(image))
            continue
        try:
            width, height = png_size(image)
            encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        except (OSError, ValueError) as exc:
            warnings.append(str(exc))
            continue
        marks = []
        for record in records:
            if record["town"] != town:
                continue
            for key in INFRACTION_KEYS:
                for description in record["infractions"][key]:
                    coord = parse_coords(description)
                    if coord is None:
                        continue
                    px, py = pixel(coord, town)
                    if not (0 <= px < width and 0 <= py < height):
                        warnings.append("{} map point out of bounds for {}: ({}, {})".format(record["route_id"], town, px, py))
                        continue
                    color = COLORS[key]
                    marks.append('<path d="M{} {}h12M{} {}h-12M{} {}v12M{} {}v-12" stroke="{}" stroke-width="2"/>'.format(
                        px - 6, py, px + 6, py, px, py - 6, px, py + 6, color))
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}">'
               '<image width="{}" height="{}" href="data:image/png;base64,{}"/>{}</svg>\n').format(
                   width, height, width, height, width, height, encoded, "".join(marks))
        target = output_dir / (town + ".svg")
        if target.exists() and not overwrite:
            fail("output exists; use --overwrite or another save directory: {}".format(target))
        target.write_text(svg, encoding="utf-8")
    legend = output_dir / "legend.svg"
    if not legend.exists() or overwrite:
        entries = []
        for index, key in enumerate(INFRACTION_KEYS):
            y = 20 + index * 22
            entries.append('<rect x="4" y="{}" width="12" height="12" fill="{}"/><text x="24" y="{}" font-size="12">{}</text>'.format(y - 12, COLORS[key], y, key))
        legend.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="260" height="{}">{}</svg>\n'.format(24 + 22 * len(entries), "".join(entries)), encoding="utf-8")
    return warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate TransFuser result JSON files; no CARLA/network execution.")
    parser.add_argument("--xml", required=True, type=Path, help="Route XML used for this result set")
    parser.add_argument("--results", required=True, nargs="+", help="JSON file(s) or directories")
    parser.add_argument("--save-dir", required=True, type=Path)
    parser.add_argument("--town-maps", type=Path, help="Optional directory with Town01.png..Town06.png")
    parser.add_argument("--failure-policy", choices=("source", "strict", "allow"), default="source")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        route_metadata = load_route_metadata(args.xml.expanduser().resolve())
        files = [load_result(path) for path in result_files(args.results)]
        records, labels, source_values, driven = collect_records(files, route_metadata, args.failure_policy)
        rows, rates = csv_rows(records, labels, source_values, driven)
        save_dir = args.save_dir.expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        csv_path = save_dir / "results.csv"
        if csv_path.exists() and not args.overwrite:
            fail("output exists; use --overwrite or another save directory: {}".format(csv_path))
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)
        map_warnings = []
        if args.town_maps:
            map_warnings = write_svg_maps(records, args.town_maps, save_dir, args.overwrite)
    except (OSError, ValueError, statistics.StatisticsError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    for warning in map_warnings:
        print("WARNING: {}".format(warning), file=sys.stderr)
    print(json.dumps({
        "csv": str(csv_path), "records": len(records), "route_count": len(route_metadata),
        "repetitions": len(records) // len(route_metadata), "driven_km": driven,
        "infraction_rates": rates, "map_warnings": map_warnings,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

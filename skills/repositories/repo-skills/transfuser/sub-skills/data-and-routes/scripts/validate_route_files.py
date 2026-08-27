#!/usr/bin/env python3
"""Validate TransFuser-style route XML and scenario JSON without CARLA.

This is a structural checker, not a route interpolator.  It never imports
CARLA, starts a server, contacts the network, or rewrites an input file.
"""
from __future__ import print_function

import argparse
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

TOWNS = frozenset(
    ["Town01", "Town02", "Town03", "Town04", "Town05", "Town06", "Town07", "Town10HD"]
)
# Structural scenario JSON validation also covers the checked-in Longest6
# evaluation annotations (Scenario1 through Scenario10). Training-data route
# generation supports a narrower subset; build_route_tool_command.py enforces
# that separate generation contract.
SCENARIOS = frozenset("Scenario1 Scenario2 Scenario3 Scenario4 Scenario5 Scenario6 Scenario7 Scenario8 Scenario9 Scenario10".split())
TRANSFORM_FIELDS = ("x", "y", "z", "yaw", "pitch")
WAYPOINT_FIELDS = ("x", "y", "z", "pitch", "roll", "yaw")


def _number(value, label, errors):
    try:
        float(value)
    except (TypeError, ValueError):
        errors.append("{} must be numeric, got {!r}".format(label, value))


def _expand_paths(values, suffixes):
    paths = []
    for value in values or []:
        if os.path.isdir(value):
            for root, dirs, files in os.walk(value):
                dirs.sort()
                for filename in sorted(files):
                    if filename.lower().endswith(suffixes):
                        paths.append(os.path.join(root, filename))
        else:
            paths.append(value)
    return sorted(set(os.path.abspath(path) for path in paths))


def validate_route_xml(path, expected_town=None):
    result = {"path": path, "kind": "route-xml", "errors": [], "warnings": [], "stats": {}}
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        result["errors"].append("cannot parse XML: {}".format(exc))
        return result

    if root.tag != "routes":
        result["errors"].append("root element must be <routes>, got <{}>".format(root.tag))
    routes = list(root.findall("route"))
    if not routes:
        result["errors"].append("file contains no <route> elements")

    ids = []
    towns = Counter()
    weather_count = 0
    waypoint_counts = Counter()
    for index, route in enumerate(routes):
        prefix = "route[{}]".format(index)
        route_id = route.attrib.get("id")
        town = route.attrib.get("town") or route.attrib.get("map")
        if not route_id:
            result["errors"].append("{} is missing id".format(prefix))
        else:
            ids.append(route_id)
        if not town:
            result["errors"].append("{} is missing town".format(prefix))
        else:
            towns[town] += 1
            if town not in TOWNS:
                result["errors"].append("{} has unsupported town {!r}".format(prefix, town))
            if expected_town and town != expected_town:
                result["errors"].append("{} town {!r} != expected {!r}".format(prefix, town, expected_town))
        waypoints = list(route.findall("waypoint"))
        waypoint_counts[len(waypoints)] += 1
        if len(waypoints) < 2:
            result["errors"].append("{} must contain at least two waypoints".format(prefix))
        for waypoint_index, waypoint in enumerate(waypoints):
            for field in WAYPOINT_FIELDS:
                if field not in waypoint.attrib:
                    result["errors"].append("{} waypoint[{}] missing {}".format(prefix, waypoint_index, field))
                else:
                    _number(waypoint.attrib[field], "{} waypoint[{}].{}".format(prefix, waypoint_index, field), result["errors"])
        weather = route.find("weather")
        if weather is not None:
            weather_count += 1
            if not weather.attrib.get("id"):
                result["errors"].append("{} weather is missing id".format(prefix))
            for field, value in weather.attrib.items():
                if field != "id":
                    _number(value, "{} weather.{}".format(prefix, field), result["errors"])

    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        result["errors"].append("duplicate route ids within file: {}".format(", ".join(duplicates)))
    if ids and any(not re.match(r"^[^\s]+$", item) for item in ids):
        result["warnings"].append("one or more route ids contain whitespace")
    result["stats"] = {
        "routes": len(routes),
        "towns": dict(sorted(towns.items())),
        "waypoint_counts": {str(k): v for k, v in sorted(waypoint_counts.items())},
        "weather_routes": weather_count,
    }
    return result


def validate_scenario_json(path, expected_scenario=None, expected_town=None):
    result = {"path": path, "kind": "scenario-json", "errors": [], "warnings": [], "stats": {}}
    try:
        with open(path, "r") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        result["errors"].append("cannot parse JSON: {}".format(exc))
        return result

    blocks = data.get("available_scenarios") if isinstance(data, dict) else None
    if not isinstance(blocks, list):
        result["errors"].append("available_scenarios must be a list")
        return result
    towns = Counter()
    scenario_types = Counter()
    events = 0
    for block_index, town_block in enumerate(blocks):
        if not isinstance(town_block, dict):
            result["errors"].append("available_scenarios[{}] must be an object".format(block_index))
            continue
        for town, scenario_list in sorted(town_block.items()):
            towns[town] += 1
            if town not in TOWNS:
                result["errors"].append("unsupported town {!r}".format(town))
            if expected_town and town != expected_town:
                result["errors"].append("town {!r} != expected {!r}".format(town, expected_town))
            if not isinstance(scenario_list, list):
                result["errors"].append("{} scenario list must be a list".format(town))
                continue
            for scenario_index, scenario in enumerate(scenario_list):
                prefix = "{} scenario[{}]".format(town, scenario_index)
                if not isinstance(scenario, dict):
                    result["errors"].append("{} must be an object".format(prefix))
                    continue
                scenario_type = scenario.get("scenario_type")
                scenario_types[scenario_type] += 1
                if scenario_type not in SCENARIOS:
                    result["errors"].append("{} has unsupported scenario_type {!r}".format(prefix, scenario_type))
                if expected_scenario and scenario_type != expected_scenario:
                    result["errors"].append("{} type {!r} != expected {!r}".format(prefix, scenario_type, expected_scenario))
                configurations = scenario.get("available_event_configurations")
                if not isinstance(configurations, list):
                    result["errors"].append("{} available_event_configurations must be a list".format(prefix))
                    continue
                for event_index, event in enumerate(configurations):
                    events += 1
                    event_prefix = "{} event[{}]".format(prefix, event_index)
                    if not isinstance(event, dict):
                        result["errors"].append("{} must be an object".format(event_prefix))
                        continue
                    transform = event.get("transform")
                    if not isinstance(transform, dict):
                        result["errors"].append("{} transform must be an object".format(event_prefix))
                    else:
                        for field in TRANSFORM_FIELDS:
                            if field not in transform:
                                result["errors"].append("{} transform missing {}".format(event_prefix, field))
                            else:
                                _number(transform[field], "{} transform.{}".format(event_prefix, field), result["errors"])
    if not blocks:
        result["warnings"].append("available_scenarios is empty")
    if events == 0:
        result["warnings"].append("scenario file contains no event configurations")
    result["stats"] = {
        "town_blocks": len(towns),
        "towns": dict(sorted(towns.items())),
        "scenario_types": dict(sorted((str(k), v) for k, v in scenario_types.items())),
        "events": events,
    }
    return result


def cross_check(route_results, scenario_results):
    scenario_towns = set()
    for result in scenario_results:
        scenario_towns.update(result.get("stats", {}).get("towns", {}).keys())
    for result in route_results:
        for town in result.get("stats", {}).get("towns", {}):
            if town not in scenario_towns:
                result["warnings"].append("no supplied scenario JSON contains route town {}".format(town))


def run_self_test():
    with tempfile.TemporaryDirectory() as root:
        xml_path = os.path.join(root, "Town03_Scenario8.xml")
        json_path = os.path.join(root, "Town03_Scenario8.json")
        ET.ElementTree(
            ET.fromstring(
                '<routes><route id="7" town="Town03">'
                '<waypoint x="0" y="0" z="0" pitch="0" roll="0" yaw="90"/>'
                '<waypoint x="1" y="2" z="0" pitch="0" roll="0" yaw="90"/>'
                '</route></routes>'
            )
        ).write(xml_path, encoding="utf-8", xml_declaration=True)
        with open(json_path, "w") as handle:
            json.dump({"available_scenarios": [{"Town03": [{
                "scenario_type": "Scenario8",
                "available_event_configurations": [{"transform": {
                    "x": 0, "y": 0, "z": 0, "yaw": 90, "pitch": 0
                }, "other_actors": None}]
            }]}]}, handle)
        route = validate_route_xml(xml_path, "Town03")
        scenario = validate_scenario_json(json_path, "Scenario8", "Town03")
        assert not route["errors"], route
        assert not scenario["errors"], scenario
        cross_check([route], [scenario])
        assert not route["warnings"], route
    return {"self_test": "passed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", nargs="+", help="route XML file(s) or directory")
    parser.add_argument("--scenarios", nargs="*", help="scenario JSON file(s) or directory")
    parser.add_argument("--town", choices=sorted(TOWNS), help="require this town in every supplied file")
    parser.add_argument("--scenario-id", choices=sorted(SCENARIOS), help="require this logical scenario type in JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true", help="run a tiny deterministic XML/JSON fixture check")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if not args.routes and not args.scenarios:
        parser.error("provide --routes and/or --scenarios, or use --self-test")

    route_results = [validate_route_xml(path, args.town) for path in _expand_paths(args.routes, (".xml",))]
    scenario_results = [validate_scenario_json(path, args.scenario_id, args.town) for path in _expand_paths(args.scenarios, (".json",))]
    cross_check(route_results, scenario_results)
    results = route_results + scenario_results
    payload = {"ok": not any(item["errors"] for item in results), "files": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "OK" if not item["errors"] else "ERROR"
            print("[{}] {} ({})".format(status, item["path"], item["kind"]))
            for message in item["errors"]:
                print("  error: {}".format(message))
            for message in item["warnings"]:
                print("  warning: {}".format(message))
            print("  stats: {}".format(json.dumps(item["stats"], sort_keys=True)))
        print("overall: {}".format("OK" if payload["ok"] else "ERROR"))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

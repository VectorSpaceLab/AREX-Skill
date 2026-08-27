#!/usr/bin/env python3
"""Build a safe, non-executing TransFuser route/data command plan.

The output is a reviewable plan for an operator who has separately supplied a
compatible runtime.  This script never starts CARLA, imports CARLA, contacts a
server, invokes a generator, or creates output directories.
"""
from __future__ import print_function

import argparse
import json
import os
import shlex
import sys
import tempfile
from types import SimpleNamespace

SCENARIO_IDS = ("Scenario1", "Scenario3", "Scenario4", "Scenario7", "Scenario8", "Scenario9", "Scenario10")
TOWNS = ("Town01", "Town02", "Town03", "Town04", "Town05", "Town06", "Town07", "Town10HD")


def _path(value):
    return os.path.abspath(os.path.expanduser(value)) if value else None


def _shell(value):
    return shlex.quote(str(value))


def _town_spec(value):
    if value == "all":
        return list(TOWNS), "all"
    towns = [item.strip() for item in value.replace(",", " ").split() if item.strip()]
    bad = sorted(set(towns) - set(TOWNS))
    if bad:
        raise ValueError("unsupported town(s): {}".format(", ".join(bad)))
    if not towns:
        raise ValueError("town selection is empty")
    return towns, ",".join(towns)


def _scenario_spec(value):
    if value == "all":
        return list(SCENARIO_IDS)
    values = [item.strip() for item in value.replace(",", " ").split() if item.strip()]
    bad = sorted(set(values) - set(SCENARIO_IDS))
    if bad:
        raise ValueError("unsupported scenario id(s): {}".format(", ".join(bad)))
    if not values:
        raise ValueError("scenario selection is empty")
    return values


def _common(args):
    runtime = _path(args.runtime_root)
    carla_root = _path(args.carla_root)
    scenario_root = _path(args.scenarios_dir or os.path.join(runtime, "leaderboard", "data", "training", "scenarios"))
    route_root = _path(args.routes_dir or os.path.join(runtime, "leaderboard", "data", "training", "routes"))
    egg = os.path.join(carla_root, "PythonAPI", "carla", "dist", "carla-0.9.10-py3.7-linux-x86_64.egg")
    scenario_runner = os.path.join(runtime, "scenario_runner")
    leaderboard = os.path.join(runtime, "leaderboard")
    pythonpath = os.pathsep.join([
        os.path.join(carla_root, "PythonAPI"),
        os.path.join(carla_root, "PythonAPI", "carla"),
        egg,
        scenario_runner,
        leaderboard,
    ])
    return {
        "runtime_root": runtime,
        "carla_root": carla_root,
        "scenarios_dir": scenario_root,
        "routes_dir": route_root,
        "scenario_runner_root": scenario_runner,
        "leaderboard_root": leaderboard,
        "carla_server": os.path.join(carla_root, "CarlaUE4.sh"),
        "pythonpath_prefix": pythonpath,
        "port": int(args.port),
    }


def _python(runtime, relative):
    return os.path.join(runtime, relative)


def _command(parts):
    return " ".join(_shell(part) for part in parts)


def _scenario_commands(common, scenarios, town_specs):
    commands = []
    for town_spec in town_specs:
        if any(item in scenarios for item in ("Scenario1", "Scenario3")):
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_scenarios/gen_scenario_1_3.py"),
                                      "--save_dir={}".format(common["scenarios_dir"]), "--towns={}".format(town_spec)]))
        if "Scenario4" in scenarios:
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_scenarios/gen_scenario_4.py"),
                                      "--save_dir={}".format(common["scenarios_dir"]), "--towns={}".format(town_spec)]))
        if any(item in scenarios for item in ("Scenario7", "Scenario8", "Scenario9")):
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_scenarios/gen_scenario_7_8_9.py"),
                                      "--save_dir={}".format(common["scenarios_dir"]), "--towns={}".format(town_spec)]))
        if "Scenario10" in scenarios:
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_scenarios/gen_scenario_10.py"),
                                      "--save_dir={}".format(common["scenarios_dir"]), "--towns={}".format(town_spec)]))
    return commands


def _route_commands(common, scenarios, town_specs, include_lane_change):
    commands = []
    for town_spec in town_specs:
        for scenario, road_type in (("Scenario1", "curved"), ("Scenario3", "curved"), ("Scenario4", "junction")):
            if scenario in scenarios:
                commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_routes/gen_routes_for_scen_1_3_4.py"),
                                          "--save_dir={}".format(common["routes_dir"]),
                                          "--scenarios_dir={}".format(os.path.join(common["scenarios_dir"], scenario)),
                                          "--town={}".format(town_spec), "--road_type={}".format(road_type)]))
        if any(item in scenarios for item in ("Scenario7", "Scenario8", "Scenario9")):
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_routes/gen_routes_for_scen_7_8_9.py"),
                                      "--save_dir={}".format(common["routes_dir"]),
                                      "--scenarios_dir={}".format(common["scenarios_dir"]),
                                      "--town={}".format(town_spec)]))
        if "Scenario10" in scenarios:
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_routes/gen_routes_for_scen_10.py"),
                                      "--save_dir={}".format(common["routes_dir"]),
                                      "--scenarios_dir={}".format(os.path.join(common["scenarios_dir"], "Scenario10")),
                                      "--town={}".format(town_spec)]))
        if include_lane_change:
            commands.append(_command(["python3", _python(common["runtime_root"], "tools/dataset/gen_routes/gen_routes_lane_change.py"),
                                      "--save_dir={}".format(common["routes_dir"]), "--town={}".format(town_spec)]))
    return commands


def build_plan(args):
    if not args.runtime_root or not args.carla_root:
        raise ValueError("--runtime-root and --carla-root are required")
    common = _common(args)
    towns, town_spec = _town_spec(args.towns)
    town_specs = ["all"] if args.towns == "all" else towns
    scenarios = _scenario_spec(args.scenario_id)
    commands = []
    environment = {
        "CARLA_ROOT": common["carla_root"],
        "CARLA_SERVER": common["carla_server"],
        "SCENARIO_RUNNER_ROOT": common["scenario_runner_root"],
        "LEADERBOARD_ROOT": common["leaderboard_root"],
        "PYTHONPATH_PREFIX": common["pythonpath_prefix"],
        "PORT": str(common["port"]),
    }
    warnings = [
        "PLAN ONLY: commands are not executed by this script",
        "CARLA 0.9.10.1 server, PythonAPI/egg, ScenarioRunner, leaderboard, and compatible runtime must be checked separately",
    ]
    if args.mode in ("scenarios", "routes", "datagen"):
        warnings.append("scenario/route generation and collection require a separately running CARLA server")
    if args.mode == "scenarios":
        commands = _scenario_commands(common, scenarios, town_specs)
    elif args.mode == "routes":
        commands = _route_commands(common, scenarios, town_specs, args.include_lane_change)
        warnings.append("scenario JSON must already exist; route generation follows scenario generation")
    elif args.mode == "datagen":
        town = args.town or (towns[0] if towns != list(TOWNS) else "Town10HD")
        if town not in TOWNS:
            raise ValueError("unsupported --town: {}".format(town))
        scenario = scenarios[0]
        if len(scenarios) != 1:
            raise ValueError("--mode datagen requires exactly one --scenario-id")
        scenario_file = os.path.join(common["scenarios_dir"], scenario, "{}_{}.json".format(town, scenario))
        route_file = os.path.join(common["routes_dir"], scenario, "{}_{}.xml".format(town, scenario))
        agent = _path(args.agent or os.path.join(common["runtime_root"], "team_code_autopilot", "data_agent.py"))
        checkpoint = _path(args.checkpoint or os.path.join(common["runtime_root"], "results", "{}_{}.json".format(town, scenario)))
        save_path = _path(args.save_path or os.path.join(common["runtime_root"], "results", "{}_{}".format(town, scenario)))
        environment.update({
            "SCENARIOS": scenario_file, "ROUTES": route_file, "REPETITIONS": "1",
            "CHALLENGE_TRACK_CODENAME": "MAP", "CHECKPOINT_ENDPOINT": checkpoint,
            "SAVE_PATH": save_path, "TEAM_AGENT": agent, "DEBUG_CHALLENGE": "0",
            "RESUME": "1", "DATAGEN": "1",
        })
        evaluator = _python(common["runtime_root"], "leaderboard/leaderboard/leaderboard_evaluator_local.py")
        parts = ["python3", evaluator, "--scenarios={}".format(scenario_file), "--routes={}".format(route_file),
                 "--repetitions=1", "--track=MAP", "--checkpoint={}".format(checkpoint),
                 "--agent={}".format(agent), "--debug=0", "--resume=1"]
        if args.team_config:
            parts.append("--agent-config={}".format(_path(args.team_config)))
            environment["TEAM_CONFIG"] = _path(args.team_config)
        commands = [_command(parts)]
        warnings.append("DATAGEN=1 writes sensor/label files and can consume substantial disk and simulator time")
    elif args.mode == "visualize":
        if not args.input_path:
            raise ValueError("--mode visualize requires --input-path")
        input_path = _path(args.input_path)
        output_dir = _path(args.output_dir or os.path.join(common["runtime_root"], "figures", "vis_points"))
        map_dir = _path(args.map_dir or os.path.join(common["runtime_root"], "leaderboard", "data", "maps"))
        commands = [_command(["python3", _python(common["runtime_root"], "tools/dataset/vis_points.py"),
                             "--in_path={}".format(input_path), "--save_dir={}".format(output_dir),
                             "--map_dir={}".format(map_dir)])]
        warnings.append("visualization requires compatible CARLA Python bindings, map-image assets, pygame, and display/headless setup")
    missing = []
    for key in ("runtime_root", "carla_root", "scenario_runner_root", "leaderboard_root"):
        if not os.path.exists(common[key]):
            missing.append(common[key])
    if args.mode == "visualize" and args.input_path and not os.path.exists(_path(args.input_path)):
        missing.append(_path(args.input_path))
    if missing:
        warnings.append("planning paths not present locally: {}".format(", ".join(sorted(set(missing)))))
    return {
        "mode": args.mode, "towns": towns, "scenarios": scenarios,
        "environment": environment,
        "server_prerequisite": "Separately verify/start a CARLA 0.9.10.1 server on localhost:{}; this plan never launches it.".format(common["port"]),
        "commands": commands, "warnings": warnings,
    }


def run_self_test():
    root = tempfile.mkdtemp(prefix="transfuser-command-")
    args = SimpleNamespace(
        mode="routes", runtime_root=os.path.join(root, "runtime"), carla_root=os.path.join(root, "carla"),
        scenarios_dir=None, routes_dir=None, towns="all", scenario_id="all", include_lane_change=True,
        port=2000, agent=None, checkpoint=None, save_path=None, team_config=None, town=None,
        input_path=None, output_dir=None, map_dir=None,
    )
    plan = build_plan(args)
    assert len(plan["commands"]) == 6, plan
    assert "Scenario1" in plan["commands"][0] and "Scenario3" in plan["commands"][1], plan
    assert "gen_routes_lane_change.py" in plan["commands"][-1], plan
    assert all("CarlaUE4.sh" not in command for command in plan["commands"]), plan
    assert "PLAN ONLY" in plan["warnings"][0], plan
    return {"self_test": "passed", "commands": len(plan["commands"])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("scenarios", "routes", "datagen", "visualize"), help="plan type")
    parser.add_argument("--runtime-root", help="operator-supplied compatible project/runtime root")
    parser.add_argument("--carla-root", help="operator-supplied CARLA 0.9.10.1 root")
    parser.add_argument("--scenarios-dir", help="scenario output/input directory")
    parser.add_argument("--routes-dir", help="route output/input directory")
    parser.add_argument("--towns", default="all", help="all or comma/space-separated Town01..Town10HD")
    parser.add_argument("--town", help="single collection/visualization town")
    parser.add_argument("--scenario-id", default="all", help="all or comma/space-separated Scenario ids")
    parser.add_argument("--include-lane-change", action="store_true", help="append lane-change route generation to a routes plan")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--agent", help="privileged data-agent file for datagen")
    parser.add_argument("--team-config", help="optional agent config path for datagen")
    parser.add_argument("--checkpoint", help="datagen checkpoint endpoint")
    parser.add_argument("--save-path", help="datagen sensor output root")
    parser.add_argument("--input-path", help="XML/JSON input for visualization")
    parser.add_argument("--output-dir", help="visualization output directory")
    parser.add_argument("--map-dir", help="CARLA-derived visualization map directory")
    parser.add_argument("--format", choices=("shell", "json"), default="shell")
    parser.add_argument("--self-test", action="store_true", help="run a deterministic command-plan fixture check")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if not args.mode:
        parser.error("--mode is required unless --self-test is used")
    try:
        plan = build_plan(args)
    except ValueError as exc:
        parser.error(str(exc))
    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print("# PLAN ONLY: review before external execution; no server is launched.")
        print("# {}".format(plan["server_prerequisite"]))
        for key, value in sorted(plan["environment"].items()):
            if key == "PYTHONPATH_PREFIX":
                print("export PYTHONPATH={}\"${{PYTHONPATH:-}}\"".format(_shell(value + os.pathsep)))
            else:
                print("export {}={}".format(key, _shell(value)))
        for command in plan["commands"]:
            print(command)
        for warning in plan["warnings"]:
            print("# WARNING: {}".format(warning))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build and preflight a TransFuser leaderboard evaluation command.

This helper is intentionally non-executing: it prints a shell plan or JSON and
never launches CARLA, the evaluator, Docker, or a network operation.

Example:
    python build_evaluation_command.py --repo-root /work/transfuser \
      --carla-root /opt/CARLA_0.9.10.1 --mode local \
      --route-set longest6 --team-config /models/transfuser \
      --checkpoint /work/results/run.json --resume true
"""

from __future__ import print_function

import argparse
import json
import os
from pathlib import Path
import shlex
import sys


def parse_bool(value):
    normalized = str(value).strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise argparse.ArgumentTypeError("expected true/false, 1/0, yes/no, or on/off")


def path_text(path):
    return str(Path(path).expanduser().resolve())


def shell_join(items):
    return " ".join(shlex.quote(str(item)) for item in items)


def add_missing(problems, label, path, kind="any"):
    candidate = Path(path)
    exists = candidate.is_dir() if kind == "dir" else candidate.is_file() if kind == "file" else candidate.exists()
    if not exists:
        problems.append("{} is missing: {}".format(label, candidate))


def find_carla_egg(carla_root):
    dist = Path(carla_root) / "PythonAPI" / "carla" / "dist"
    patterns = (
        "carla-0.9.10*-py3*.egg",
        "carla-0.9.10*.egg",
        "carla*-py3*.egg",
        "carla*.egg",
    )
    for pattern in patterns:
        matches = sorted(dist.glob(pattern)) if dist.is_dir() else []
        if matches:
            return matches[0]
    return dist / "carla-0.9.10-py3.7-linux-x86_64.egg"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Print a preflighted TransFuser CARLA evaluation plan; never execute it."
    )
    parser.add_argument("--repo-root", required=True, help="TransFuser checkout root")
    parser.add_argument("--carla-root", required=True, help="External CARLA 0.9.10.1 root")
    parser.add_argument("--mode", choices=("local", "upstream"), default="local",
                        help="Local preserves TransFuser Longest6 changes")
    parser.add_argument("--route-set", choices=("longest6", "split", "custom"), default="longest6")
    parser.add_argument("--route-index", type=int, help="Longest6 split index, 0 through 35")
    parser.add_argument("--routes", help="Custom route XML; required for --route-set custom")
    parser.add_argument("--scenarios", help="Custom scenario JSON; defaults to Longest6 scenarios")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--track", choices=("SENSORS", "MAP"), default="SENSORS")
    parser.add_argument("--checkpoint", help="Result/checkpoint JSON path")
    parser.add_argument("--team-agent", help="Agent Python file")
    parser.add_argument("--team-config", help="Agent config/model directory")
    parser.add_argument("--debug", type=int, default=0)
    parser.add_argument("--resume", type=parse_bool, default=True,
                        metavar="BOOL", help="True emits --resume=True; false omits the legacy flag")
    parser.add_argument("--record", help="Optional external CARLA recorder output directory")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--traffic-manager-port", type=int, default=8000)
    parser.add_argument("--traffic-manager-seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--format", choices=("shell", "json", "argv"), default="shell")
    parser.add_argument("--allow-missing", action="store_true",
                        help="Demote missing-path errors to warnings for planning only")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.repetitions < 1:
        raise SystemExit("error: --repetitions must be positive")
    if args.debug < 0:
        raise SystemExit("error: --debug must be nonnegative")
    if not 1 <= args.port <= 65535 or not 1 <= args.traffic_manager_port <= 65535:
        raise SystemExit("error: ports must be in 1..65535")
    if args.timeout <= 0:
        raise SystemExit("error: --timeout must be positive")
    if args.route_set == "split" and (args.route_index is None or not 0 <= args.route_index <= 35):
        raise SystemExit("error: --route-set split requires --route-index in 0..35")
    if args.route_set != "split" and args.route_index is not None:
        raise SystemExit("error: --route-index is valid only with --route-set split")
    if args.route_set == "custom" and not args.routes:
        raise SystemExit("error: --route-set custom requires --routes")
    if args.route_set != "custom" and args.routes:
        raise SystemExit("error: --routes is valid only with --route-set custom")

    repo_root = Path(args.repo_root).expanduser().resolve()
    carla_root = Path(args.carla_root).expanduser().resolve()
    scenario_runner_root = repo_root / "scenario_runner"
    leaderboard_root = repo_root / "leaderboard"

    default_scenarios = leaderboard_root / "data" / "longest6" / "eval_scenarios.json"
    scenarios = Path(args.scenarios).expanduser().resolve() if args.scenarios else default_scenarios

    if args.route_set == "longest6":
        routes = leaderboard_root / "data" / "longest6" / "longest6.xml"
    elif args.route_set == "split":
        routes = (leaderboard_root / "data" / "longest6" / "longest6_split" /
                  "longest_weathers_{}.xml".format(args.route_index))
    else:
        routes = Path(args.routes).expanduser().resolve()

    team_agent = (Path(args.team_agent).expanduser().resolve() if args.team_agent else
                  repo_root / "team_code_transfuser" / "submission_agent.py")
    team_config = (Path(args.team_config).expanduser().resolve() if args.team_config else
                   repo_root / "model_ckpt" / "transfuser")
    checkpoint = (Path(args.checkpoint).expanduser().resolve() if args.checkpoint else
                  repo_root / "results" / "transfuser_longest6.json")

    evaluator_name = "leaderboard_evaluator_local.py" if args.mode == "local" else "leaderboard_evaluator.py"
    evaluator = leaderboard_root / "leaderboard" / evaluator_name
    carla_egg = find_carla_egg(carla_root)

    missing = []
    add_missing(missing, "repository root", repo_root, "dir")
    add_missing(missing, "CARLA server", carla_root / "CarlaUE4.sh", "file")
    add_missing(missing, "CARLA PythonAPI", carla_root / "PythonAPI" / "carla", "dir")
    add_missing(missing, "CARLA Python egg", carla_egg, "file")
    add_missing(missing, "ScenarioRunner package", scenario_runner_root / "srunner", "dir")
    add_missing(missing, "leaderboard evaluator", evaluator, "file")
    add_missing(missing, "scenario annotations", scenarios, "file")
    add_missing(missing, "route XML", routes, "file")
    add_missing(missing, "team agent", team_agent, "file")
    add_missing(missing, "team config", team_config)
    if not checkpoint.parent.is_dir():
        missing.append("checkpoint parent directory is missing: {}".format(checkpoint.parent))

    warnings = []
    if args.allow_missing:
        warnings.extend(missing)
        missing = []
    if args.mode == "upstream" and args.route_set in ("longest6", "split"):
        warnings.append("upstream mode does not preserve documented Longest6 dense-traffic/no-stop-penalty semantics")
    if args.resume and not checkpoint.is_file():
        warnings.append("resume requested but checkpoint does not exist; evaluator resume state will be empty")
    if not args.resume and checkpoint.exists():
        warnings.append("fresh run selected and checkpoint exists; the evaluator can truncate it")
    if args.track == "MAP" and team_agent.name == "submission_agent.py":
        warnings.append("default learned submission agent declares the SENSORS track; MAP may be rejected")

    if missing:
        for item in missing:
            print("ERROR: {}".format(item), file=sys.stderr)
        print("No command emitted. Use --allow-missing only for a non-runnable planning artifact.", file=sys.stderr)
        return 2

    pythonpath = [
        carla_root / "PythonAPI",
        carla_root / "PythonAPI" / "carla",
        carla_egg,
        scenario_runner_root,
        leaderboard_root,
    ]

    env = {
        "CARLA_ROOT": str(carla_root),
        "CARLA_SERVER": str(carla_root / "CarlaUE4.sh"),
        "SCENARIO_RUNNER_ROOT": str(scenario_runner_root),
        "LEADERBOARD_ROOT": str(leaderboard_root),
        "SCENARIOS": str(scenarios),
        "ROUTES": str(routes),
        "REPETITIONS": str(args.repetitions),
        "TRACK": args.track,
        "CHALLENGE_TRACK_CODENAME": args.track,
        "CHECKPOINT": str(checkpoint),
        "CHECKPOINT_ENDPOINT": str(checkpoint),
        "TEAM_AGENT": str(team_agent),
        "TEAM_CONFIG": str(team_config),
        "DEBUG": str(args.debug),
        "DEBUG_CHALLENGE": str(args.debug),
        "RESUME": "1" if args.resume else "0",
        "DATAGEN": "0",
    }

    command = [
        "python3", str(evaluator),
        "--host={}".format(args.host),
        "--port={}".format(args.port),
        "--trafficManagerPort={}".format(args.traffic_manager_port),
        "--trafficManagerSeed={}".format(args.traffic_manager_seed),
        "--timeout={}".format(args.timeout),
        "--scenarios={}".format(scenarios),
        "--routes={}".format(routes),
        "--repetitions={}".format(args.repetitions),
        "--track={}".format(args.track),
        "--checkpoint={}".format(checkpoint),
        "--agent={}".format(team_agent),
        "--agent-config={}".format(team_config),
        "--debug={}".format(args.debug),
    ]
    if args.record:
        command.append("--record={}".format(path_text(args.record)))
    if args.resume:
        command.append("--resume=True")

    plan = {
        "schema": "transfuser.evaluation-plan.v1",
        "executes": False,
        "mode": args.mode,
        "route_set": args.route_set,
        "environment": env,
        "pythonpath_prepend": [str(path) for path in pythonpath],
        "argv": command,
        "warnings": warnings,
        "external_requirements": [
            "CARLA 0.9.10.1 server",
            "matching CARLA PythonAPI and evaluator dependencies",
            "agent-compatible GPU/model runtime",
        ],
    }

    for warning in warnings:
        print("WARNING: {}".format(warning), file=sys.stderr)

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    elif args.format == "argv":
        print(json.dumps(command, indent=2))
    else:
        print("# Generated plan only; review before running in the external CARLA runtime.")
        for key in sorted(env):
            print("export {}={}".format(key, shlex.quote(env[key])))
        prefix = ":".join(str(path) for path in pythonpath)
        print("export PYTHONPATH={}:\"${{PYTHONPATH:-}}\"".format(shlex.quote(prefix)))
        print(shell_join(command))

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read-only preflight for the TransFuser Docker submission tree.

No Docker, network, credential, or file-copy operation is performed.
"""

from __future__ import print_function

import argparse
import json
from pathlib import Path
import sys

SECRET_NAMES = (".env", ".aws", ".ssh", "id_rsa", "credentials", "token", "secret", "kubeconfig")


def exists(errors, label, path, directory=None):
    path = Path(path)
    ok = path.is_dir() if directory is True else path.is_file() if directory is False else path.exists()
    if not ok:
        errors.append("{} missing: {}".format(label, path))
    return ok


def inspect(args):
    errors, warnings = [], []
    carla = Path(args.carla_root).expanduser().resolve()
    scenario = Path(args.scenario_runner_root).expanduser().resolve()
    leaderboard = Path(args.leaderboard_root).expanduser().resolve()
    team = Path(args.team_code_root).expanduser().resolve()
    config = Path(args.config_dir).expanduser().resolve() if args.config_dir else team / "model_ckpt" / "transfuser"

    exists(errors, "CARLA root", carla, True)
    exists(errors, "CARLA server", carla / "CarlaUE4.sh", False)
    pythonapi = carla / "PythonAPI" / "carla"
    exists(errors, "CARLA PythonAPI package", pythonapi, True)
    dist = pythonapi / "dist"
    exists(errors, "CARLA egg directory", dist, True)
    eggs = sorted(dist.glob("*.egg")) if dist.is_dir() else []
    if not eggs:
        errors.append("CARLA PythonAPI has no .egg in {}".format(dist))
    else:
        py3 = [egg for egg in eggs if "py3" in egg.name or "cp3" in egg.name]
        py2 = [egg for egg in eggs if "py2" in egg.name or "cp2" in egg.name]
        if not py3:
            warnings.append("no Python 3-named CARLA egg found in {}".format(dist))
        if not py2:
            warnings.append("no Python 2-named CARLA egg found; source staging script expects both classes")

    exists(errors, "ScenarioRunner root", scenario, True)
    exists(errors, "ScenarioRunner package", scenario / "srunner", True)
    exists(errors, "leaderboard root", leaderboard, True)
    exists(errors, "leaderboard package", leaderboard / "leaderboard", True)
    exists(errors, "master Dockerfile", leaderboard / "scripts" / "Dockerfile.master", False)
    exists(errors, "container evaluation script", leaderboard / "scripts" / "run_evaluation.sh", False)
    exists(errors, "team code root", team, True)
    for filename in ("submission_agent.py", "requirements.txt"):
        exists(errors, "team code {}".format(filename), team / filename, False)
    exists(errors, "model config directory", config, True)
    args_file = config / "args.txt"
    if exists(errors, "model args.txt", args_file, False):
        try:
            with args_file.open(encoding="utf-8") as handle:
                parsed = json.load(handle)
            if not isinstance(parsed, dict):
                errors.append("{} must contain a JSON object".format(args_file))
        except (OSError, ValueError) as exc:
            errors.append("{} is not valid JSON: {}".format(args_file, exc))
    checkpoints = sorted(config.glob("*.pth")) if config.is_dir() else []
    if not checkpoints:
        errors.append("no .pth checkpoint found in {}".format(config))
    else:
        empty = [str(path) for path in checkpoints if path.stat().st_size == 0]
        if empty:
            errors.append("empty checkpoint(s): {}".format(", ".join(empty)))

    if args.require_local_server and not (carla / "CarlaUE4.sh").is_file():
        errors.append("--require-local-server requested but CarlaUE4.sh is unavailable")

    try:
        for path in team.rglob("*"):
            relative = path.relative_to(team)
            lowered = str(relative).lower()
            if any(token in lowered for token in SECRET_NAMES):
                warnings.append("secret-like path under team code: {}".format(relative))
            if path.is_symlink():
                try:
                    path.resolve().relative_to(team)
                except ValueError:
                    errors.append("symlink escapes team-code root: {} -> {}".format(relative, path.resolve()))
    except OSError as exc:
        warnings.append("could not fully scan team code for secret-like paths: {}".format(exc))

    return {
        "schema": "transfuser.submission-layout.v1",
        "checked": {
            "carla_root": str(carla),
            "scenario_runner_root": str(scenario),
            "leaderboard_root": str(leaderboard),
            "team_code_root": str(team),
            "config_dir": str(config),
        },
        "checkpoint_count": len(checkpoints),
        "errors": errors,
        "warnings": warnings,
        "docker_or_network_invoked": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check Docker submission layout without building or uploading.")
    parser.add_argument("--carla-root", required=True)
    parser.add_argument("--scenario-runner-root", required=True)
    parser.add_argument("--leaderboard-root", required=True)
    parser.add_argument("--team-code-root", required=True)
    parser.add_argument("--config-dir")
    parser.add_argument("--require-local-server", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    report = inspect(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for label, path in report["checked"].items():
            print("{}: {}".format(label, path))
        print("checkpoints: {}".format(report["checkpoint_count"]))
        for warning in report["warnings"]:
            print("WARNING: {}".format(warning), file=sys.stderr)
        for error in report["errors"]:
            print("ERROR: {}".format(error), file=sys.stderr)
        print("Docker/network invoked: no")
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

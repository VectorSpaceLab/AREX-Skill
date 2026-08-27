#!/usr/bin/env python3
"""Run bundled DRL-Pytorch no-training smoke diagnostics.

This wrapper dispatches to the generated sub-skill smoke scripts. It requires a
user-supplied DRL-Pytorch checkout via --repo-root, but it does not depend on the
checkout used to create this skill. The default mode avoids Gymnasium optional
environment creation, ROM downloads, rendering, TensorBoard, multiprocessing,
and training loops.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_MAP = {
    "value": SKILL_ROOT / "sub-skills" / "value-based-discrete-control" / "scripts" / "smoke_value_based.py",
    "policy": SKILL_ROOT / "sub-skills" / "policy-and-actor-critic-control" / "scripts" / "smoke_policy_control.py",
    "atari": SKILL_ROOT / "sub-skills" / "atari-and-asl-workflows" / "scripts" / "smoke_atari_asl.py",
}


def run_script(label: str, script: Path, repo_root: Path, extra_args: list[str]) -> int:
    if not script.is_file():
        print(f"FAIL {label}: missing bundled script {script}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(script), "--repo-root", str(repo_root), *extra_args]
    print("\n==>", label, "::", " ".join(cmd))
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DRL-Pytorch bundled no-training smoke diagnostics.")
    parser.add_argument("--repo-root", type=Path, required=True, help="Path to a DRL-Pytorch checkout to inspect.")
    parser.add_argument(
        "--suite",
        choices=["value", "policy", "atari", "all"],
        default="all",
        help="Which sub-skill smoke suite to run. Default: all.",
    )
    parser.add_argument(
        "--value-algorithm",
        default="all",
        help="Forwarded to value smoke --algorithm when suite includes value. Default: all.",
    )
    parser.add_argument(
        "--policy-algorithm",
        default="all",
        help="Forwarded to policy smoke --algorithm when suite includes policy. Default: all.",
    )
    parser.add_argument(
        "--ppo-distribution",
        default="all",
        choices=["Beta", "GS_ms", "GS_m", "all"],
        help="Forwarded to policy smoke when PPO-Continuous is checked. Default: all.",
    )
    parser.add_argument("--probe-atari-wrappers", action="store_true", help="Forward optional Atari wrapper import probe.")
    parser.add_argument("--probe-envpool", action="store_true", help="Forward optional EnvPool import probe.")
    parser.add_argument("--probe-asl-sharer", action="store_true", help="Forward optional tiny ASL shared-data probe.")
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Return non-zero if optional Atari/EnvPool/ASL probes fail. Required smokes are always strict.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        print(f"FAIL: --repo-root is not a directory: {args.repo_root}", file=sys.stderr)
        return 2

    selected = ["value", "policy", "atari"] if args.suite == "all" else [args.suite]
    failures = 0

    if "value" in selected:
        failures += int(run_script("value", SCRIPT_MAP["value"], repo_root, ["--algorithm", args.value_algorithm]) != 0)
    if "policy" in selected:
        failures += int(
            run_script(
                "policy",
                SCRIPT_MAP["policy"],
                repo_root,
                ["--algorithm", args.policy_algorithm, "--ppo-distribution", args.ppo_distribution],
            )
            != 0
        )
    if "atari" in selected:
        atari_args: list[str] = []
        if args.probe_atari_wrappers:
            atari_args.append("--probe-atari-wrappers")
        if args.probe_envpool:
            atari_args.append("--probe-envpool")
        if args.probe_asl_sharer:
            atari_args.append("--probe-asl-sharer")
        if args.strict_optional:
            atari_args.append("--strict-optional")
        failures += int(run_script("atari", SCRIPT_MAP["atari"], repo_root, atari_args) != 0)

    if failures:
        print(f"FAIL: {failures} smoke suite(s) failed", file=sys.stderr)
        return 1
    print("\nOK: selected DRL-Pytorch smoke suites passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

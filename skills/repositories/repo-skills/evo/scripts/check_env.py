#!/usr/bin/env python3
"""Quick evo environment smoke check.

Run this from any working directory after installing evo. It imports the public
package and a few core submodules, then runs safe `--help` checks for the main
console entry points.

Optional:
- --repo-root PATH: prepend a local checkout to sys.path before imports.
- --skip-cli: only run the Python import checks.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def bootstrap_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    path = Path(repo_root).resolve()
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def run_help(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"missing console script: {command}")
    proc = subprocess.run(
        [command, "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{command} --help failed with exit {proc.returncode}:\n{proc.stdout}{proc.stderr}"
        )
    print(f"ok: {command} --help")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout to add to sys.path before imports.")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Only run the Python import checks.",
    )
    args = parser.parse_args()

    bootstrap_repo_root(args.repo_root)

    import evo
    from evo.core import metrics, sync, trajectory
    from evo.tools import file_interface, pandas_bridge

    print(f"ok: imported evo {evo.__version__}")
    print("ok: imported evo.core.metrics, evo.core.sync, evo.core.trajectory")
    print("ok: imported evo.tools.file_interface, evo.tools.pandas_bridge")
    print(f"ok: pose relation = {metrics.PoseRelation.translation_part.value}")
    print(f"ok: plane = {trajectory.Plane.XY.value}")
    _ = sync.matching_time_indices
    _ = file_interface.read_tum_trajectory_file
    _ = pandas_bridge.trajectory_to_df

    if not args.skip_cli:
        for command in ["evo", "evo_ape", "evo_rpe", "evo_traj", "evo_res", "evo_config"]:
            run_help(command)
        if shutil.which("evo") is not None:
            proc = subprocess.run(
                ["evo", "pkg", "--version"],
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"evo pkg --version failed with exit {proc.returncode}:\n{proc.stdout}{proc.stderr}"
                )
            print(f"ok: evo pkg --version -> {proc.stdout.strip()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

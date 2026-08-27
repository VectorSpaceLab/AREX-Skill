#!/usr/bin/env python3
"""Build and run a tiny Brian2 C++ standalone project in a temporary directory.

This is a post-environment-preparation smoke, not an import-only check. It
requires the active Brian2 installation and a working C++ build toolchain.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a one-neuron Brian2 cpp_standalone project in a temporary "
            "directory, assert monitor output, and clean it up."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="describe the smoke without importing Brian2 or compiling",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        print("planned: tiny cpp_standalone build in a temporary directory")
        return 0

    # Keep the package import after argument parsing so --help and --dry-run
    # remain useful when compiled Brian2 support is not available yet.
    import numpy as np
    from brian2 import NeuronGroup, StateMonitor, defaultclock, device, ms, run
    from brian2.devices.device import reset_device, set_device

    defaultclock.dt = 0.1 * ms
    try:
        with tempfile.TemporaryDirectory(prefix="brian2_standalone_smoke_") as temp:
            project_dir = Path(temp)
            try:
                set_device(
                    "cpp_standalone",
                    build_on_run=False,
                    directory=str(project_dir),
                    with_output=False,
                )
                group = NeuronGroup(
                    1,
                    "dv/dt = -v / tau : 1\n tau : second (shared, constant)",
                    method="exact",
                    name="smoke_group",
                )
                group.tau = 1 * ms
                group.v = 1.0
                monitor = StateMonitor(group, "v", record=True, name="smoke_monitor")
                run(0.2 * ms)

                # This is deliberately a real native build/run. The model and
                # duration are tiny; no external data is used.
                device.build(
                    directory=str(project_dir),
                    results_directory="results",
                    compile=True,
                    run=True,
                    with_output=False,
                )
                assert device.project_dir == str(project_dir)
                assert monitor.v.shape[0] == 1
                assert monitor.v.shape[1] > 0
                assert np.isfinite(np.asarray(monitor.v)).all()
                print(
                    "standalone smoke passed: "
                    f"{monitor.v.shape[1]} samples in {project_dir.name}"
                )
            finally:
                # Delete Brian-owned files while the temporary project still
                # exists, then restore the process-wide runtime device.
                try:
                    device.delete(force=True)
                except Exception:
                    pass
                try:
                    reset_device()
                except Exception:
                    pass
    except Exception:
        # TemporaryDirectory removes any partial project even when compilation
        # or the native executable fails before Brian can finish cleanup.
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a safe local LabML tracking smoke test.

This script records a tiny experiment in a temporary project path, exercises
`experiment.record`, `tracker.save`, `monit.loop`, and `logger.log`, and then
prints the resolved LabML paths. It expects the installed `labml` package to
be available on the Python path.

Example:
    python scripts/tracking_smoke.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from labml import experiment, lab, logger, monit, tracker


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="labml-tracking-smoke-") as tmp:
        project_root = Path(tmp)
        lab_conf = {
            "path": str(project_root),
            "data_path": "data",
            "experiments_path": "logs",
            "app_url": None,
            "check_repo_dirty": False,
        }
        with experiment.record(name="tracking-smoke", writers={"screen", "file"}, lab_conf=lab_conf):
            tracker.set_scalar("loss", is_print=True)
            tracker.set_scalar("accuracy", is_print=True)
            for step in monit.loop(3):
                tracker.save(step, {
                    "loss": 1.0 / (step + 1),
                    "accuracy": step / 3.0,
                })
                logger.log(f"smoke step={step}")

        print(f"project_root={lab.get_path()}")
        print(f"data_path={lab.get_data_path()}")
        print(f"experiments_path={lab.get_experiments_path()}")
        print(f"lab_info={lab.get_info()['configs']['path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

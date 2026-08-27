#!/usr/bin/env python3
"""Credential-safe SwanLab disabled-mode tracking smoke check."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def main() -> int:
    import swanlab

    if swanlab.run is not None or swanlab.has_run():
        raise AssertionError("expected no active SwanLab run before smoke check")

    with tempfile.TemporaryDirectory(prefix="swanlab-disabled-smoke-") as tmp:
        old_cwd = os.getcwd()
        os.chdir(tmp)
        try:
            log_dir = Path(tmp) / "swanlog-disabled-should-not-exist"
            run = swanlab.init(
                mode="disabled",
                project="disabled-smoke",
                log_dir=str(log_dir),
                config={"learning_rate": 0.001, "batch_size": 2},
            )
            assert swanlab.has_run(), "has_run() should be true after init"
            assert swanlab.run is run, "swanlab.run should return the active run"
            assert swanlab.get_run() is run, "get_run() should return the active run"
            assert run.mode == "disabled", f"expected disabled mode, got {run.mode!r}"

            swanlab.log({"loss": 0.25, "acc": 0.75}, step=0)
            run.log({"train": {"loss": 0.2, "acc": 0.8}}, step=1)
            run.config["checked"] = True

            swanlab.finish()
            assert not swanlab.has_run(), "has_run() should be false after finish"
            assert swanlab.run is None, "swanlab.run should reset to None after finish"

            try:
                swanlab.get_run()
            except RuntimeError:
                pass
            else:
                raise AssertionError("get_run() should fail after finish")

            assert not log_dir.exists(), "disabled mode should not create the configured log_dir"
        finally:
            os.chdir(old_cwd)

    print("swanlab disabled tracking smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

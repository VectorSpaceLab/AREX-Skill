#!/usr/bin/env python3
"""Smoke-test Sacred core experiment behavior without external services.

The script creates a tiny interactive=True experiment, verifies config injection
and explicit captured-argument overrides, tracks temporary resource/artifact
files during an active run, logs scalar metrics, exercises programmatic and
argument-vector execution, and asserts Run results.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sacred import Experiment, Ingredient, __version__ as SACRED_VERSION


def build_experiment(tmpdir: Path) -> Experiment:
    data = Ingredient("data", interactive=True, save_git_info=False)
    data.add_config(scale=3, offset=1)

    @data.capture
    def transform(value, scale, offset):
        return value * scale + offset

    @data.command(unobserved=True)
    def describe(scale, offset):
        return {"scale": scale, "offset": offset}

    ex = Experiment(
        "disco_experiment_core_smoke",
        ingredients=[data],
        interactive=True,
        save_git_info=False,
    )
    ex.add_config(base=2, label="demo")

    @ex.capture
    def add_base(value, base):
        return value + base

    @ex.command(unobserved=True)
    def alternate(base):
        return base * 10

    @ex.main
    def main(base, label, _run, _config, _log):
        assert _run is not None
        assert _log is not None
        assert _config["base"] == base

        injected = transform(base)
        overridden = transform(base, scale=5)
        captured_override = add_base(10, base=1)

        resource_path = tmpdir / "input.txt"
        resource_path.write_text("abc", encoding="utf-8")
        with ex.open_resource(str(resource_path), "r") as handle:
            resource_text = handle.read()
        ex.add_resource(str(resource_path))

        artifact_path = tmpdir / "result.json"
        artifact_path.write_text(
            json.dumps({"injected": injected, "overridden": overridden}),
            encoding="utf-8",
        )
        ex.add_artifact(
            str(artifact_path),
            name="result.json",
            metadata={"kind": "smoke"},
            content_type="application/json",
        )
        _run.add_artifact(str(artifact_path), name="result-via-run.json")

        ex.log_scalar("smoke.score", injected, step=0)
        _run.log_scalar("smoke.score", overridden, step=1)
        _run.info["label"] = label

        return {
            "injected": injected,
            "overridden": overridden,
            "captured_override": captured_override,
            "resource_text": resource_text,
        }

    return ex


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sacred-smoke-") as tmp:
        ex = build_experiment(Path(tmp))

        run = ex.run(config_updates={"base": 4, "data": {"scale": 6}})
        assert run.status == "COMPLETED"
        assert run.config["base"] == 4
        assert run.config["data"]["scale"] == 6
        assert run.result == {
            "injected": 25,          # base=4, data.scale=6, data.offset=1
            "overridden": 21,        # explicit scale=5 overrides config scale=6
            "captured_override": 11, # explicit base=1 overrides config base=4
            "resource_text": "abc",
        }
        assert run.info["label"] == "demo"

        ingredient_command = ex.run(
            command_name="data.describe",
            config_updates={"data": {"offset": 2}},
        )
        assert ingredient_command.status == "COMPLETED"
        assert ingredient_command.result == {"scale": 3, "offset": 2}

        root_command = ex.run(command_name="alternate", config_updates={"base": 7})
        assert root_command.status == "COMPLETED"
        assert root_command.result == 70

        cli_command = ex.run_commandline(argv=["sacred_experiment_smoke.py", "alternate"])
        assert cli_command is not None
        assert cli_command.status == "COMPLETED"
        assert cli_command.result == 20

    print(f"OK: Sacred experiment-core smoke passed with sacred {SACRED_VERSION}")


if __name__ == "__main__":
    main()

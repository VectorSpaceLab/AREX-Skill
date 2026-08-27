#!/usr/bin/env python3
"""Run a safe local Sacred FileStorageObserver probe.

The probe uses only temporary files, no network, no credentials, no services,
and no source-checkout dependency. It imports the installed ``sacred`` package,
creates a tiny experiment, logs run info and scalar metrics, registers one
resource and one artifact, and asserts the expected local observer files.

Example:
    python scripts/sacred_file_observer_probe.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Sacred FileStorageObserver local run metadata, metrics, artifact, and resource writes."
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the temporary probe directory and print its path for debugging",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def find_run_dir(runs_dir: Path, run_id: Any) -> Path:
    candidate = runs_dir / str(run_id)
    if candidate.is_dir():
        return candidate
    run_dirs = [p for p in runs_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]
    require(len(run_dirs) == 1, f"expected exactly one run directory, found {[p.name for p in run_dirs]}")
    return run_dirs[0]


def run_probe(keep_temp: bool = False) -> int:
    try:
        from sacred import Experiment
        from sacred.observers import FileStorageObserver
    except Exception as exc:  # pragma: no cover - exercised only in broken environments
        print(
            "IMPORT_ERROR: could not import Sacred and FileStorageObserver. "
            "Install Sacred 0.8.7 with its base dependencies before running this probe. "
            f"Original error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    temp_root = Path(tempfile.mkdtemp(prefix="sacred-file-observer-probe-"))
    try:
        runs_dir = temp_root / "runs"
        resource_file = temp_root / "input-resource.txt"
        artifact_file = temp_root / "artifact-output.txt"
        resource_text = "alpha\nbeta\n"
        resource_file.write_text(resource_text, encoding="utf-8")

        ex = Experiment("file-observer-probe")
        ex.observers.append(FileStorageObserver(runs_dir))

        @ex.config
        def cfg():
            factor = 2
            label = "probe"

        @ex.main
        def main(_run, factor, label):
            with _run.open_resource(str(resource_file), "r") as handle:
                payload = handle.read()

            _run.info["resource_chars"] = len(payload)
            ex.info["label"] = label
            _run.log_scalar("probe.loss", 0.25, step=2)
            ex.log_scalar("probe.accuracy", 0.9)

            artifact_file.write_text(payload.upper() * factor, encoding="utf-8")
            _run.add_artifact(
                str(artifact_file),
                name="artifact-output.txt",
                metadata={"kind": "probe"},
                content_type="text/plain",
            )
            return len(payload) * factor

        run = ex.run(options={"--loglevel": "ERROR"})
        run_dir = find_run_dir(runs_dir, run._id)

        required_files = ["run.json", "config.json", "cout.txt", "info.json", "metrics.json"]
        for filename in required_files:
            require((run_dir / filename).is_file(), f"missing {filename}")

        config = load_json(run_dir / "config.json")
        require(config["factor"] == 2, "config.json did not preserve factor")
        require(config["label"] == "probe", "config.json did not preserve label")

        run_json = load_json(run_dir / "run.json")
        require(run_json["status"] == "COMPLETED", f"unexpected status {run_json.get('status')}")
        require(run_json["result"] == len(resource_text) * 2, "run.json result mismatch")
        require(run_json["command"] == "main", "run.json command mismatch")
        require("artifact-output.txt" in run_json.get("artifacts", []), "artifact not listed in run.json")
        require(run_json.get("resources"), "resource not listed in run.json")
        require(run_json.get("heartbeat"), "heartbeat timestamp missing from run.json")

        stored_artifact = run_dir / "artifact-output.txt"
        require(stored_artifact.is_file(), "artifact file was not copied into run directory")
        require(stored_artifact.read_text(encoding="utf-8") == resource_text.upper() * 2, "artifact content mismatch")

        original_resource, stored_resource_name = run_json["resources"][0]
        require(Path(original_resource).name == resource_file.name, "resource original filename mismatch")
        stored_resource = Path(stored_resource_name)
        if not stored_resource.is_absolute():
            stored_resource = runs_dir / stored_resource
        require(stored_resource.is_file(), "stored resource copy does not exist")
        require(stored_resource.read_text(encoding="utf-8") == resource_text, "stored resource content mismatch")

        info = load_json(run_dir / "info.json")
        require(info["resource_chars"] == len(resource_text), "info.json resource_chars mismatch")
        require(info["label"] == "probe", "info.json label mismatch")

        metrics = load_json(run_dir / "metrics.json")
        for metric_name in ["probe.loss", "probe.accuracy"]:
            require(metric_name in metrics, f"missing metric {metric_name}")
            require(set(metrics[metric_name]) == {"steps", "values", "timestamps"}, f"unexpected metric keys for {metric_name}")
            require(len(metrics[metric_name]["timestamps"]) == len(metrics[metric_name]["values"]), f"timestamp/value length mismatch for {metric_name}")
        require(metrics["probe.loss"]["steps"] == [2], "explicit step metric mismatch")
        require(metrics["probe.loss"]["values"] == [0.25], "explicit value metric mismatch")
        require(metrics["probe.accuracy"]["steps"] == [0], "implicit step metric mismatch")
        require(metrics["probe.accuracy"]["values"] == [0.9], "implicit value metric mismatch")

        print(
            "PROBE_OK "
            f"run_id={run._id} "
            "files=run.json,config.json,info.json,metrics.json,artifact,resource"
        )
        if keep_temp:
            print(f"TEMP_DIR={temp_root}")
        return 0
    except Exception as exc:
        if keep_temp:
            print(f"TEMP_DIR={temp_root}", file=sys.stderr)
        print(f"PROBE_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    args = parse_args()
    return run_probe(keep_temp=args.keep_temp)


if __name__ == "__main__":
    raise SystemExit(main())

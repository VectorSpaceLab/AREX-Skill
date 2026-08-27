#!/usr/bin/env python3
"""Safe Sacred environment/API smoke check.

Run with the same Python that will execute Sacred experiments:

    python scripts/sacred_env_check.py
    python scripts/sacred_env_check.py --json

The check imports Sacred, inspects key public signatures, runs a tiny
in-process experiment with a local FileStorageObserver, and reports optional
observer dependencies without starting services or using credentials.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import pathlib
import tempfile
import warnings


def _optional_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def run_check() -> dict:
    warnings.filterwarnings("ignore", category=UserWarning, module="sacred.dependencies")
    import sacred
    from sacred import Experiment, Ingredient, SETTINGS
    from sacred.observers import FileStorageObserver

    signatures = {
        "Experiment.__init__": str(inspect.signature(Experiment.__init__)),
        "Experiment.run": str(inspect.signature(Experiment.run)),
        "Experiment.run_commandline": str(inspect.signature(Experiment.run_commandline)),
        "Experiment.add_artifact": str(inspect.signature(Experiment.add_artifact)),
        "Experiment.log_scalar": str(inspect.signature(Experiment.log_scalar)),
        "Ingredient.__init__": str(inspect.signature(Ingredient.__init__)),
        "Ingredient.capture": str(inspect.signature(Ingredient.capture)),
        "Ingredient.command": str(inspect.signature(Ingredient.command)),
        "Ingredient.add_config": str(inspect.signature(Ingredient.add_config)),
        "FileStorageObserver.__init__": str(inspect.signature(FileStorageObserver.__init__)),
    }

    ex = Experiment("sacred_env_check", interactive=True)

    @ex.config
    def cfg():
        base = 2
        multiplier = 5

    @ex.capture
    def calc(base, multiplier):
        return base * multiplier

    @ex.main
    def main(_run):
        fd, artifact = tempfile.mkstemp(prefix="sacred-env-check-", suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write("artifact-ok")
            _run.add_artifact(artifact, name="artifact.txt")
            _run.log_scalar("score", calc(), step=1)
            _run.info["status"] = "ok"
            return calc()
        finally:
            try:
                os.remove(artifact)
            except OSError:
                pass

    with tempfile.TemporaryDirectory(prefix="sacred-env-check-") as run_root:
        ex.observers.append(FileStorageObserver(run_root))
        run = ex.run(config_updates={"base": 3})
        run_dirs = [p for p in pathlib.Path(run_root).iterdir() if p.is_dir() and not p.name.startswith("_")]
        if not run_dirs:
            raise AssertionError("FileStorageObserver did not create a run directory")
        run_dir = run_dirs[0]
        required = ["run.json", "config.json", "info.json", "metrics.json", "artifact.txt"]
        missing = [name for name in required if not (run_dir / name).exists()]
        if missing:
            raise AssertionError(f"Missing expected FileStorageObserver files: {missing}")

    optional_dependencies = {
        "pymongo_for_mongo_observer": _optional_module("pymongo"),
        "sqlalchemy_for_sql_observer": _optional_module("sqlalchemy"),
        "tinydb_for_tinydb_observer": _optional_module("tinydb"),
        "hashfs_for_tinydb_observer": _optional_module("hashfs"),
        "boto3_for_s3_observer": _optional_module("boto3"),
        "google_cloud_storage_for_gcs_observer": _optional_module("google.cloud.storage"),
        "tensorflow_for_stflow": _optional_module("tensorflow"),
    }

    return {
        "ok": True,
        "sacred_version": getattr(sacred, "__version__", "unknown"),
        "result": run.result,
        "settings_groups": sorted(k for k in dir(SETTINGS) if k.isupper()),
        "signatures": signatures,
        "optional_dependencies": optional_dependencies,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe Sacred import/API/local-observer smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a short text summary.")
    args = parser.parse_args()
    result = run_check()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        missing_optional = [k for k, present in result["optional_dependencies"].items() if not present]
        print(f"SACRED_ENV_CHECK_OK sacred={result['sacred_version']} result={result['result']}")
        print("Optional dependencies not installed:", ", ".join(missing_optional) if missing_optional else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a safe ZenML pipeline-authoring smoke check."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any

ZENML_ENV_PREFIXES = ("ZENML_STORE_",)
ZENML_ISOLATION_ENV = {
    "ZENML_ANALYTICS_OPT_IN": "false",
    "MLSTACKS_ANALYTICS_OPT_OUT": "true",
    "AUTO_OPEN_DASHBOARD": "false",
    "ZENML_ENABLE_RICH_TRACEBACK": "false",
}


def _clear_remote_store_environment() -> None:
    for key in list(os.environ):
        if key.startswith(ZENML_ENV_PREFIXES):
            os.environ.pop(key, None)


def _set_isolated_environment(root: Path) -> None:
    os.environ.update(ZENML_ISOLATION_ENV)
    os.environ["ZENML_CONFIG_PATH"] = str(root / "zenml_config")
    os.environ["ZENML_LOCAL_STORES_PATH"] = str(root / "zenml_local_stores")
    os.environ["ZENML_REPOSITORY_PATH"] = str(root / "repo")
    _clear_remote_store_environment()


def check_imports() -> dict[str, Any]:
    imports: dict[str, str] = {}
    try:
        import zenml
        from zenml import ArtifactConfig, pipeline, step, unmapped, wait
        from zenml.config import DockerSettings, ResourceSettings, Schedule
        from zenml.materializers.base_materializer import BaseMaterializer

        imports["zenml"] = getattr(zenml, "__version__", "imported")
        imports["pipeline"] = pipeline.__name__
        imports["step"] = step.__name__
        imports["wait"] = wait.__name__
        imports["unmapped"] = unmapped.__name__
        imports["ArtifactConfig"] = ArtifactConfig.__name__
        imports["DockerSettings"] = DockerSettings.__name__
        imports["ResourceSettings"] = ResourceSettings.__name__
        imports["Schedule"] = Schedule.__name__
        imports["BaseMaterializer"] = BaseMaterializer.__name__
    except Exception as exc:  # pragma: no cover - diagnostic output path
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "imports": imports,
        }

    return {"ok": True, "imports": imports}


def run_pipeline_smoke(root: Path) -> dict[str, Any]:
    _set_isolated_environment(root)
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    from zenml import pipeline, step
    from zenml.client import Client

    Client.initialize(repo)
    os.chdir(repo)

    @step(enable_cache=False)
    def produce_name() -> str:
        return "ZenML"

    @step(enable_cache=False)
    def build_greeting(name: str) -> Annotated[str, "greeting"]:
        return f"Hello {name}"

    @pipeline(enable_cache=False)
    def smoke_pipeline() -> Annotated[str, "greeting"]:
        return build_greeting(produce_name())

    run = smoke_pipeline.with_options(run_name="pipeline-authoring-smoke")()
    result: dict[str, Any] = {
        "ok": True,
        "run_returned": run is not None,
        "repository_initialized": (repo / ".zen").exists(),
    }
    if run is not None:
        result["run_name"] = getattr(run, "name", None)
        result["run_status"] = str(getattr(run, "status", "unknown"))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check ZenML imports or run an opt-in tiny local pipeline inside "
            "an isolated temporary ZenML configuration."
        )
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Only verify core pipeline-authoring imports. This is the default.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run a tiny local pipeline using temporary ZenML config and stores.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary directory after --run for debugging.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    return parser.parse_args()


def _print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    if result.get("ok"):
        print("ZenML pipeline smoke check passed.")
        for key, value in result.items():
            if key != "ok":
                print(f"- {key}: {value}")
    else:
        print("ZenML pipeline smoke check failed.")
        print(f"- error: {result.get('error', 'unknown error')}")


def main() -> int:
    args = parse_args()
    if not args.run:
        result = check_imports()
        _print_result(result, args.json)
        return 0 if result.get("ok") else 1

    temp_root = Path(tempfile.mkdtemp(prefix="zenml-pipeline-smoke-"))
    try:
        result = run_pipeline_smoke(temp_root)
        if args.keep_temp:
            result["temp_root"] = str(temp_root)
        _print_result(result, args.json)
        return 0 if result.get("ok") else 1
    except Exception as exc:  # pragma: no cover - diagnostic output path
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.keep_temp:
            result["temp_root"] = str(temp_root)
        _print_result(result, args.json)
        return 1
    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

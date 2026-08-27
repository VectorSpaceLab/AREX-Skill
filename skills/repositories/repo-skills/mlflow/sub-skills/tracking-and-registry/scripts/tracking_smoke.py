#!/usr/bin/env python3
"""Safe local MLflow tracking smoke test.

This script uses an isolated SQLite tracking URI by default because modern
MLflow versions place filesystem tracking backends in maintenance mode.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from random import Random


def _sqlite_uri(path: Path) -> str:
    return f"sqlite:///{path.absolute().resolve()}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe local MLflow tracking smoke test with params, metrics, tags, artifacts, and search.",
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help="Tracking URI to use. Defaults to a temporary SQLite database.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Directory for the temporary SQLite DB and artifacts. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--experiment-name",
        default="agent-skill-tracking-smoke",
        help="Experiment name to create or reuse.",
    )
    parser.add_argument(
        "--run-name",
        default="tracking-smoke-run",
        help="Run name to log.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed for deterministic metric values.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary work directory and print its location.",
    )
    parser.add_argument(
        "--registry-probe",
        action="store_true",
        help="Also try a metadata-only registered-model create/delete probe against the same SQLite store.",
    )
    return parser.parse_args()


def run_smoke(args: argparse.Namespace) -> dict[str, object]:
    try:
        import mlflow
        from mlflow import MlflowClient
    except ModuleNotFoundError as exc:
        if exc.name == "mlflow":
            raise SystemExit(
                "MLflow is not importable. Install MLflow in the active Python environment, "
                "then rerun this smoke script."
            ) from exc
        raise

    temp_context = None
    if args.work_dir is None:
        temp_context = tempfile.TemporaryDirectory(prefix="mlflow-tracking-smoke-")
        work_dir = Path(temp_context.name)
    else:
        work_dir = args.work_dir
    work_dir.mkdir(parents=True, exist_ok=True)

    tracking_uri = args.tracking_uri or _sqlite_uri(work_dir / "mlflow.db")
    artifact_dir = work_dir / "artifacts"
    artifact_dir.mkdir(exist_ok=True)

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)

    rng = Random(args.seed)
    experiment = mlflow.set_experiment(args.experiment_name)
    client = MlflowClient()

    with tempfile.TemporaryDirectory(prefix="mlflow-smoke-artifacts-") as artifact_tmp:
        output_dir = Path(artifact_tmp) / "outputs"
        output_dir.mkdir()
        (output_dir / "test.txt").write_text("hello world!\n", encoding="utf-8")
        (output_dir / "metrics.json").write_text(
            json.dumps({"seed": args.seed, "source": "tracking_smoke.py"}, indent=2),
            encoding="utf-8",
        )

        with mlflow.start_run(run_name=args.run_name) as run:
            run_id = run.info.run_id
            mlflow.log_param("param1", rng.randint(0, 100), synchronous=True)
            mlflow.set_tag("agent_skill.smoke", "true", synchronous=True)
            for step in range(3):
                mlflow.log_metric("foo", rng.random() + step, step=step, synchronous=True)
            mlflow.log_artifacts(str(output_dir), artifact_path="outputs")
            artifact_uri = mlflow.get_artifact_uri("outputs/test.txt")

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="tags.agent_skill.smoke = 'true'",
        output_format="list",
    )
    matching_run_ids = {result.info.run_id for result in runs}
    if run_id not in matching_run_ids:
        raise RuntimeError(f"Logged run {run_id} was not returned by search_runs")

    artifacts = client.list_artifacts(run_id, "outputs")
    artifact_paths = sorted(item.path for item in artifacts)
    expected_artifact = "outputs/test.txt"
    if expected_artifact not in artifact_paths:
        raise RuntimeError(f"Expected {expected_artifact!r} in artifacts, got {artifact_paths!r}")

    registry_result = "skipped"
    if args.registry_probe:
        model_name = f"agent_skill_tracking_smoke_{run_id.replace('-', '_')}"
        try:
            client.create_registered_model(
                model_name,
                tags={"agent_skill.smoke": "true"},
                description="Temporary registry metadata probe from tracking_smoke.py",
            )
            fetched = client.get_registered_model(model_name)
            if fetched.name != model_name:
                raise RuntimeError(f"Registry probe fetched wrong model: {fetched.name}")
            client.delete_registered_model(model_name)
            registry_result = "created-and-deleted"
        except Exception as exc:
            registry_result = f"failed: {exc.__class__.__name__}: {exc}"

    summary = {
        "tracking_uri": tracking_uri,
        "experiment_id": experiment.experiment_id,
        "run_id": run_id,
        "artifact_uri": artifact_uri,
        "artifact_paths": artifact_paths,
        "search_matches": len(runs),
        "registry_probe": registry_result,
    }

    print(json.dumps(summary, indent=2, sort_keys=True))

    if temp_context is not None:
        if args.keep_temp:
            print(f"Kept temporary work directory: {work_dir}")
        else:
            temp_context.cleanup()

    return summary


def main() -> None:
    args = parse_args()
    run_smoke(args)


if __name__ == "__main__":
    main()

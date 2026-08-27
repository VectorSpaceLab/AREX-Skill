#!/usr/bin/env python3
"""Safe PyCaret run-lifecycle smoke.

Boots the FastAPI app with a temporary SQLite DB/artifact directory, creates a
workspace/project/experiment, submits a bounded sklearn-iris run, waits for it,
and reports Run/Trial/Event state. Use --plan setup for the fastest check or
--plan create to verify trial artifact creation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run a temp-dir PyCaret run lifecycle smoke.")
    p.add_argument(
        "--plan",
        choices=("setup", "create", "compare"),
        default="setup",
        help="run plan to submit; setup is fastest, create verifies one trial artifact",
    )
    p.add_argument("--model-id", default="lr", help="model id for --plan create")
    p.add_argument(
        "--compare-models",
        default="lr,dt",
        help="comma-separated include_models for --plan compare",
    )
    p.add_argument("--timeout-s", type=float, default=120.0, help="wait timeout in seconds")
    p.add_argument("--fold", type=int, default=2, help="CV fold in experiment setup_params")
    p.add_argument("--email", default="admin@example.com", help="bootstrap admin email")
    p.add_argument("--password", default="supersecret", help="bootstrap admin password")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON")
    p.add_argument("--keep-temp", action="store_true", help="keep temporary runtime directory")
    return p


def _configure_temp_runtime(root: Path) -> dict[str, str]:
    db_path = root / "pycaret-run-smoke.db"
    artifact_dir = root / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    try:
        from cryptography.fernet import Fernet
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("cryptography is required by pycaret-server") from exc

    env = {
        "PYCARET_DATABASE_URL": f"sqlite:///{db_path}",
        "PYCARET_ARTIFACT_DIR": str(artifact_dir),
        "PYCARET_JWT_SECRET": "test-secret-32-bytes-long-string!!",
        "PYCARET_SECRETS_KEY": Fernet.generate_key().decode(),
        "PYCARET_RUNS_BACKEND": "inprocess",
        "PYCARET_STORAGE_BACKEND": "local",
    }
    os.environ.update(env)

    from pycaret_server.config import get_settings

    get_settings.cache_clear()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from pycaret_server.db import session as sess_mod

    sess_mod.engine = create_engine(
        env["PYCARET_DATABASE_URL"],
        connect_args={"check_same_thread": False},
        future=True,
    )
    sess_mod.session_factory = sessionmaker(
        bind=sess_mod.engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    import pycaret_server.db as db_pkg

    db_pkg.engine = sess_mod.engine
    db_pkg.session_factory = sess_mod.session_factory

    _reset_singletons()

    from pycaret_server.db import Base

    Base.metadata.create_all(sess_mod.engine)
    return env


def _reset_singletons() -> None:
    names = [
        ("pycaret_server.crypto", "reset_for_tests"),
        ("pycaret_server.storage", "reset_for_tests"),
        ("pycaret_server.llm.router", "reset_router"),
        ("pycaret_server.runs.orchestrator", "reset_orchestrator"),
        ("pycaret_server.scheduler", "shutdown_scheduler"),
        ("pycaret_server.serving", "reset_registry"),
        ("pycaret_server.runtime", "reset_for_tests"),
    ]
    for module_name, attr in names:
        try:
            module = __import__(module_name, fromlist=[attr])
            getattr(module, attr)()
        except Exception:  # noqa: BLE001
            pass
    try:
        from pycaret_server.runs.broker import event_broker

        event_broker.clear()
    except Exception:  # noqa: BLE001
        pass


def _headers(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _run(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    _configure_temp_runtime(root)

    try:
        from fastapi.testclient import TestClient
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "FastAPI TestClient/httpx is unavailable; install test dependencies "
            "such as pycaret-server[test]."
        ) from exc

    from pycaret_server import __version__
    from pycaret_server.app import create_app

    with TestClient(create_app()) as client:
        boot = client.post(
            "/api/v1/setup/bootstrap",
            json={
                "email": args.email,
                "password": args.password,
                "workspace_name": "Default",
            },
        )
        if boot.status_code != 201:
            return {"ok": False, "stage": "bootstrap", "status": boot.status_code, "body": boot.text}
        tokens = boot.json()
        headers = _headers(tokens)

        ws = client.get("/api/v1/workspaces", headers=headers)
        workspace_id = ws.json()[0]["id"]

        project = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=headers,
            json={"name": "Smoke Project", "tags": ["smoke"]},
        )
        if project.status_code != 201:
            return {"ok": False, "stage": "project", "status": project.status_code, "body": project.text}
        project_id = project.json()["id"]

        exp = client.post(
            f"/api/v1/projects/{project_id}/experiments",
            headers=headers,
            json={
                "name": "iris-baseline",
                "task": "classification",
                "target": "target",
                "setup_params": {
                    "session_id": 42,
                    "fold": int(args.fold),
                    "verbose": False,
                },
            },
        )
        if exp.status_code != 201:
            return {"ok": False, "stage": "experiment", "status": exp.status_code, "body": exp.text}
        experiment_id = exp.json()["id"]

        body: dict[str, Any] = {"plan": args.plan, "sklearn_dataset": "iris"}
        if args.plan == "create":
            body["model_id"] = args.model_id
            body["plan_params"] = {"verbose": False}
        elif args.plan == "compare":
            include = [x.strip() for x in args.compare_models.split(",") if x.strip()]
            body["plan_params"] = {"include_models": include or ["lr", "dt"]}

        submitted = client.post(
            f"/api/v1/experiments/{experiment_id}/runs",
            headers=headers,
            json=body,
        )
        if submitted.status_code != 202:
            return {"ok": False, "stage": "submit", "status": submitted.status_code, "body": submitted.text}
        run_id = submitted.json()["id"]

        waited = client.post(
            f"/api/v1/runs/{run_id}/wait?timeout_s={float(args.timeout_s)}",
            headers=headers,
        )
        if waited.status_code != 200:
            return {"ok": False, "stage": "wait", "status": waited.status_code, "body": waited.text}
        run = waited.json()

        events = client.get(f"/api/v1/runs/{run_id}/events?tail=true&limit=50", headers=headers)
        trials = client.get(f"/api/v1/runs/{run_id}/trials", headers=headers)

        trial_items = trials.json().get("items", []) if trials.status_code == 200 else []
        event_items = events.json() if events.status_code == 200 else []
        artifact_trials = [t for t in trial_items if t.get("has_artifact")]

        predict_status: int | None = None
        predict_body: dict[str, Any] | None = None
        if args.plan == "create" and artifact_trials and run.get("status") == "succeeded":
            first = artifact_trials[0]
            row = {
                "sepal length (cm)": 5.1,
                "sepal width (cm)": 3.5,
                "petal length (cm)": 1.4,
                "petal width (cm)": 0.2,
            }
            pred = client.post(
                f"/api/v1/runs/{run_id}/trials/{first['id']}/predict",
                headers=headers,
                json={"rows": [row]},
            )
            predict_status = pred.status_code
            try:
                predict_body = pred.json()
            except Exception:  # noqa: BLE001
                predict_body = {"text": pred.text}

    ok = run.get("status") == "succeeded"
    if args.plan == "create":
        ok = ok and len(artifact_trials) >= 1 and predict_status == 200
    elif args.plan == "compare":
        ok = ok and len(trial_items) >= 1

    return {
        "ok": ok,
        "pycaret_server_version": __version__,
        "plan": args.plan,
        "workspace_id": workspace_id,
        "project_id": project_id,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "run_status": run.get("status"),
        "run_error": run.get("error"),
        "duration_ms": run.get("duration_ms"),
        "trial_count": len(trial_items),
        "artifact_trial_count": len(artifact_trials),
        "event_count_tail": len(event_items),
        "event_kinds_tail": [e.get("kind") for e in event_items[-10:]],
        "predict_status": predict_status,
        "predict_keys": sorted((predict_body or {}).keys()) if predict_body else None,
        "temp_root": str(root) if args.keep_temp else None,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(tempfile.mkdtemp(prefix="pycaret-run-smoke-"))
    cleanup = not args.keep_temp
    try:
        result = _run(args, root)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"pycaret run smoke ok={result.get('ok')} plan={result.get('plan')}")
            for key in (
                "run_status",
                "run_error",
                "trial_count",
                "artifact_trial_count",
                "event_count_tail",
                "predict_status",
            ):
                print(f"  {key:22} {result.get(key)}")
            if args.keep_temp:
                print(f"  temp_root              {root}")
        return 0 if result.get("ok") else 1
    except Exception as exc:  # noqa: BLE001
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 2
    finally:
        try:
            _reset_singletons()
        except Exception:  # noqa: BLE001
            pass
        if cleanup:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

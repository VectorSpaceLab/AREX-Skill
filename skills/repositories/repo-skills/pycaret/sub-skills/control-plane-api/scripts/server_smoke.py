#!/usr/bin/env python3
"""Safe PyCaret server TestClient smoke.

Creates a temporary SQLite database and artifact directory, boots the FastAPI app
in-process, checks health/setup/auth routes, and prints a concise summary. It
does not touch the caller's default pycaret.db or artifacts directory.
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
    p = argparse.ArgumentParser(description="Run a temp-dir PyCaret server smoke test.")
    p.add_argument("--email", default="admin@example.com", help="bootstrap admin email")
    p.add_argument("--password", default="supersecret", help="bootstrap admin password")
    p.add_argument("--workspace", default="Default", help="bootstrap workspace name")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON")
    p.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the temporary DB/artifact directory and include its path in output",
    )
    return p


def _configure_temp_runtime(root: Path) -> dict[str, str]:
    db_path = root / "pycaret-smoke.db"
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

    # Keep package-level exports coherent if the package was imported earlier.
    import pycaret_server.db as db_pkg

    db_pkg.engine = sess_mod.engine
    db_pkg.session_factory = sess_mod.session_factory

    _reset_singletons()

    from pycaret_server.db import Base

    Base.metadata.create_all(sess_mod.engine)
    return env


def _reset_singletons() -> None:
    resetters = []
    try:
        from pycaret_server.crypto import reset_for_tests as reset_crypto

        resetters.append(reset_crypto)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.storage import reset_for_tests as reset_storage

        resetters.append(reset_storage)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.llm.router import reset_router

        resetters.append(reset_router)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.runs.orchestrator import reset_orchestrator

        resetters.append(reset_orchestrator)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.scheduler import shutdown_scheduler

        resetters.append(shutdown_scheduler)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.serving import reset_registry

        resetters.append(reset_registry)
    except Exception:  # noqa: BLE001
        pass
    try:
        from pycaret_server.runtime import reset_for_tests as reset_gpu

        resetters.append(reset_gpu)
    except Exception:  # noqa: BLE001
        pass

    for fn in resetters:
        fn()

    try:
        from pycaret_server.runs.broker import event_broker

        event_broker.clear()
    except Exception:  # noqa: BLE001
        pass


def _run_smoke(args: argparse.Namespace, root: Path) -> dict[str, Any]:
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
        health = client.get("/healthz")
        root_resp = client.get("/")
        setup_before = client.get("/api/v1/setup/status")
        bootstrap = client.post(
            "/api/v1/setup/bootstrap",
            json={
                "email": args.email,
                "password": args.password,
                "workspace_name": args.workspace,
            },
        )
        token = bootstrap.json().get("access_token") if bootstrap.status_code < 400 else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        me = client.get("/api/v1/auth/me", headers=headers)
        workspaces = client.get("/api/v1/workspaces", headers=headers)
        openapi = client.get("/openapi.json")

    checks = {
        "healthz": health.status_code == 200 and health.json() == {"ok": True},
        "root": root_resp.status_code == 200 and bool(root_resp.json().get("version")),
        "setup_status": setup_before.status_code == 200
        and setup_before.json().get("is_bootstrapped") is False,
        "bootstrap": bootstrap.status_code == 201 and bool(token),
        "auth_me": me.status_code == 200 and me.json().get("email") == args.email,
        "workspaces": workspaces.status_code == 200 and len(workspaces.json()) == 1,
        "openapi": openapi.status_code == 200 and bool(openapi.json().get("paths")),
    }
    ok = all(checks.values())
    return {
        "ok": ok,
        "pycaret_server_version": __version__,
        "checks": checks,
        "status_codes": {
            "healthz": health.status_code,
            "root": root_resp.status_code,
            "setup_status": setup_before.status_code,
            "bootstrap": bootstrap.status_code,
            "auth_me": me.status_code,
            "workspaces": workspaces.status_code,
            "openapi": openapi.status_code,
        },
        "workspace_count": len(workspaces.json()) if workspaces.status_code == 200 else None,
        "temp_root": str(root) if args.keep_temp else None,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.keep_temp:
        root = Path(tempfile.mkdtemp(prefix="pycaret-server-smoke-"))
        cleanup = False
    else:
        root = Path(tempfile.mkdtemp(prefix="pycaret-server-smoke-"))
        cleanup = True
    try:
        result = _run_smoke(args, root)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"pycaret-server smoke ok={result['ok']}")
            for name, passed in result["checks"].items():
                print(f"  {name:14} {'OK' if passed else 'FAIL'}")
            if args.keep_temp:
                print(f"  temp_root      {root}")
        return 0 if result["ok"] else 1
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

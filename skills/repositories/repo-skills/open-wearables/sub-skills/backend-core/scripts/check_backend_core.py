#!/usr/bin/env python3
"""Safe backend-core checker for the Open Wearables repo skill.

Default checks are static and read-only: file inventory, pyproject metadata,
route module presence, docs navigation shape, and native test candidate files.
Use --import-openapi only when backend dependencies are available; it imports the
FastAPI app with harmless fallback settings, builds the OpenAPI schema, and
compares External:* endpoints with docs/docs.json. It does not call the network
or write application files.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import importlib.util
import io
import json
import logging
import os
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 is not expected here.
    tomllib = None  # type: ignore[assignment]


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

EXPECTED_ROUTE_MODULES = [
    "api_keys",
    "applications",
    "archival",
    "auth",
    "config",
    "connections",
    "dashboard",
    "data_sources",
    "developers",
    "events",
    "health_scores",
    "import_xml",
    "invitations",
    "meta",
    "oauth",
    "outgoing_webhooks",
    "priorities",
    "sdk_logs",
    "sdk_sync",
    "sdk_token",
    "seed_data",
    "summaries",
    "sync_data",
    "sync_status",
    "token",
    "user_invitation_code",
    "users",
    "vendor_workouts",
    "webhooks",
]

CORE_DEPENDENCIES = [
    "fastapi",
    "sqlalchemy",
    "psycopg",
    "pydantic-settings",
    "celery",
    "redis",
    "alembic",
    "svix",
    "boto3",
    "bcrypt",
    "python-jose",
]

DEV_DEPENDENCIES = ["pytest", "testcontainers"]

REQUIRED_FILES = [
    "backend/pyproject.toml",
    "backend/app/main.py",
    "backend/app/api/__init__.py",
    "backend/app/api/routes/v1/__init__.py",
    "backend/app/config.py",
    "backend/app/database.py",
    "backend/app/services/__init__.py",
    "backend/app/services/services.py",
    "backend/app/repositories/repositories.py",
    "backend/app/models/user.py",
    "backend/app/models/data_source.py",
    "backend/app/models/data_point_series.py",
    "backend/app/models/event_record.py",
    "backend/app/models/health_score.py",
    "backend/app/schemas/model_crud/user_management/user.py",
    "backend/app/schemas/model_crud/activities/data_point_series.py",
    "backend/app/schemas/sync_status.py",
    "backend/app/schemas/webhooks/event_types.py",
    "backend/tests/conftest.py",
    "backend/config/.env.example",
    "docs/docs.json",
]

TEST_CANDIDATES = [
    "backend/tests/api/v1/test_users.py",
    "backend/tests/api/v1/test_api_keys.py",
    "backend/tests/api/v1/test_applications.py",
    "backend/tests/api/v1/test_auth.py",
    "backend/tests/api/v1/test_token.py",
    "backend/tests/api/v1/test_sdk_token.py",
    "backend/tests/api/v1/test_connections.py",
    "backend/tests/api/v1/test_summaries.py",
    "backend/tests/api/v1/test_workouts.py",
    "backend/tests/api/v1/test_sync_data.py",
    "backend/tests/api/v1/test_sync_status.py",
    "backend/tests/api/v1/test_outgoing_webhooks.py",
    "backend/tests/api/v1/test_seed_data.py",
    "backend/tests/services/test_summaries_service.py",
    "backend/tests/services/test_time_series_service.py",
    "backend/tests/services/test_sync_status_service.py",
    "backend/tests/services/test_seed_data_service.py",
    "backend/tests/tasks/test_sync_vendor_data_task.py",
    "backend/tests/tasks/test_webhook_push_task.py",
]

EXPECTED_DOC_ENDPOINTS = [
    "GET /api/v1/users",
    "POST /api/v1/users",
    "GET /api/v1/users/{user_id}",
    "GET /api/v1/users/{user_id}/connections",
    "GET /api/v1/users/{user_id}/summaries/activity",
    "GET /api/v1/users/{user_id}/summaries/body",
    "GET /api/v1/users/{user_id}/timeseries",
    "GET /api/v1/users/{user_id}/events/workouts",
    "GET /api/v1/users/{user_id}/health-scores",
    "GET /api/v1/users/{user_id}/data-sources",
    "GET /api/v1/meta/coverage",
    "POST /api/v1/providers/{provider}/users/{user_id}/sync",
    "POST /api/v1/providers/{provider}/users/{user_id}/sync/historical",
    "GET /api/v1/users/{user_id}/sync/stream",
    "GET /api/v1/sync/runs",
    "GET /api/v1/webhooks/event-types",
    "POST /api/v1/webhooks/endpoints",
]

ENV_EXAMPLE_KEYS = [
    "SECRET_KEY",
    "DB_HOST",
    "REDIS_HOST",
    "API_BASE_URL",
    "OUTGOING_WEBHOOKS_ENABLED",
    "SVIX_SERVER_URL",
    "AWS_BUCKET_NAME",
    "RAW_PAYLOAD_STORAGE",
    "HISTORICAL_SYNC_ON_CONNECT",
]


@dataclass
class CheckReport:
    ok: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    def add_ok(self, message: str) -> None:
        self.ok.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def rel(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def find_repo_root(start: Path | None) -> Path:
    if start is not None:
        root = start.expanduser().resolve()
        if root.is_file():
            root = root.parent
        return root
    cur = Path.cwd().resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "backend" / "app" / "main.py").exists() and (candidate / "backend" / "pyproject.toml").exists():
            return candidate
    return cur


def load_docs_pages(repo_root: Path, report: CheckReport) -> set[str]:
    docs_path = repo_root / "docs" / "docs.json"
    if not docs_path.exists():
        report.add_error("docs/docs.json is missing")
        return set()
    try:
        docs = json.loads(docs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.add_error(f"docs/docs.json is not valid JSON: {exc}")
        return set()

    tabs = docs.get("navigation", {}).get("tabs", [])
    api_tabs = [tab for tab in tabs if tab.get("tab") == "API Reference"]
    if not api_tabs:
        report.add_error("docs/docs.json has no API Reference tab")
        return set()

    def flatten_pages(items: list[Any]) -> list[str]:
        out: list[str] = []
        for item in items:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                out.extend(flatten_pages(item.get("pages", [])))
        return out

    pages: list[str] = []
    for group in api_tabs[0].get("groups", []):
        pages.extend(flatten_pages(group.get("pages", [])))
    endpoint_pages = {page for page in pages if re.match(r"^(GET|POST|PUT|PATCH|DELETE) /", page)}
    report.info["docs_endpoint_pages"] = len(endpoint_pages)
    return endpoint_pages


def check_required_files(repo_root: Path, report: CheckReport) -> None:
    missing = [p for p in REQUIRED_FILES if not (repo_root / p).exists()]
    if missing:
        for p in missing:
            report.add_error(f"Missing required file: {p}")
    else:
        report.add_ok(f"Found {len(REQUIRED_FILES)} required backend/docs files")


def check_pyproject(repo_root: Path, report: CheckReport) -> None:
    pyproject = repo_root / "backend" / "pyproject.toml"
    if not pyproject.exists() or tomllib is None:
        report.add_warning("Cannot parse backend/pyproject.toml")
        return
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception as exc:
        report.add_error(f"backend/pyproject.toml parse failed: {exc}")
        return

    project = data.get("project", {})
    report.info["project_name"] = project.get("name")
    report.info["project_version"] = project.get("version")
    requires_python = project.get("requires-python", "")
    if ">=3.13" not in requires_python:
        report.add_warning(f"Unexpected requires-python value: {requires_python!r}")
    else:
        report.add_ok("backend pyproject requires Python 3.13+")

    deps = [str(dep).split("[", 1)[0].split(">", 1)[0].split("=", 1)[0].split("<", 1)[0] for dep in project.get("dependencies", [])]
    deps_text = "\n".join(project.get("dependencies", []))
    missing_core = [dep for dep in CORE_DEPENDENCIES if dep not in deps_text]
    if missing_core:
        report.add_warning(f"Core dependency names not found in pyproject: {', '.join(missing_core)}")
    else:
        report.add_ok(f"Found core backend dependencies ({len(CORE_DEPENDENCIES)})")
    report.info["dependency_count"] = len(deps)

    dep_groups = data.get("dependency-groups", {})
    dev_text = "\n".join(dep_groups.get("dev", []))
    missing_dev = [dep for dep in DEV_DEPENDENCIES if dep not in dev_text]
    if missing_dev:
        report.add_warning(f"Dev/test dependency names not found in dev group: {', '.join(missing_dev)}")
    else:
        report.add_ok("Found pytest and testcontainers in dev dependency group")

    ruff = data.get("tool", {}).get("ruff", {})
    if ruff.get("line-length") == 120:
        report.add_ok("Ruff line length is 120")
    else:
        report.add_warning("Ruff line length is not the expected 120")


def parse_route_decorators(route_file: Path) -> list[tuple[str, str, str]]:
    try:
        tree = ast.parse(route_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    endpoints: list[tuple[str, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in HTTP_METHODS:
                path = "<dynamic>"
                if dec.args:
                    try:
                        path = ast.literal_eval(dec.args[0])
                    except Exception:
                        path = ast.unparse(dec.args[0])
                endpoints.append((dec.func.attr.upper(), str(path), node.name))
    return endpoints


def check_routes(repo_root: Path, report: CheckReport) -> None:
    route_dir = repo_root / "backend" / "app" / "api" / "routes" / "v1"
    init_file = route_dir / "__init__.py"
    if not route_dir.exists() or not init_file.exists():
        report.add_error("backend/app/api/routes/v1 is missing")
        return
    source = init_file.read_text(encoding="utf-8")
    missing_imports = [mod for mod in EXPECTED_ROUTE_MODULES if f"from .{mod} import" not in source]
    if missing_imports:
        report.add_warning(f"v1 router does not import expected modules: {', '.join(missing_imports)}")
    else:
        report.add_ok(f"v1 router imports {len(EXPECTED_ROUTE_MODULES)} expected route modules")

    py_files = sorted(p for p in route_dir.glob("*.py") if p.name != "__init__.py")
    endpoints: list[tuple[str, str, str, str]] = []
    trailing_roots: list[str] = []
    for p in py_files:
        for method, path, fn in parse_route_decorators(p):
            endpoints.append((p.name, method, path, fn))
            if path == "/":
                trailing_roots.append(f"{p.name}:{fn}")
    report.info["route_modules"] = len(py_files)
    report.info["static_route_decorators"] = len(endpoints)
    if len(endpoints) < 80:
        report.add_warning(f"Static route decorator count is low: {len(endpoints)}")
    else:
        report.add_ok(f"Parsed {len(endpoints)} route decorators across {len(py_files)} v1 modules")
    if trailing_roots:
        report.add_warning("Route decorators with '/' root found; check prefixed-router redirect risk: " + ", ".join(trailing_roots))
    else:
        report.add_ok("No route module uses '/' as a route root")


def check_docs(repo_root: Path, report: CheckReport) -> set[str]:
    pages = load_docs_pages(repo_root, report)
    if pages:
        report.add_ok(f"docs/docs.json API Reference contains {len(pages)} endpoint pages")
    missing_expected = [endpoint for endpoint in EXPECTED_DOC_ENDPOINTS if endpoint not in pages]
    if missing_expected:
        report.add_warning("Expected external endpoint pages missing from docs/docs.json: " + "; ".join(missing_expected))
    else:
        report.add_ok("Expected key external endpoint pages are present in docs/docs.json")
    return pages


def check_env_example(repo_root: Path, report: CheckReport) -> None:
    env_example = repo_root / "backend" / "config" / ".env.example"
    if not env_example.exists():
        report.add_error("backend/config/.env.example is missing")
        return
    text = env_example.read_text(encoding="utf-8")
    missing = [key for key in ENV_EXAMPLE_KEYS if key not in text]
    if missing:
        report.add_warning("Expected env example keys not found: " + ", ".join(missing))
    else:
        report.add_ok("Backend env example includes core DB/Redis/auth/API/Svix/AWS settings")


def check_tests(repo_root: Path, report: CheckReport) -> None:
    missing = [p for p in TEST_CANDIDATES if not (repo_root / p).exists()]
    if missing:
        report.add_warning("Native backend test candidate files missing: " + "; ".join(missing))
    else:
        report.add_ok(f"Found {len(TEST_CANDIDATES)} native backend test candidate files")


def import_openapi(repo_root: Path, docs_pages: set[str], report: CheckReport) -> None:
    backend_dir = repo_root / "backend"
    if not backend_dir.exists():
        report.add_error("Cannot import OpenAPI: backend directory missing")
        return

    missing_import_deps = [name for name in ("fastapi", "sqlalchemy", "pydantic_settings") if importlib.util.find_spec(name) is None]
    if missing_import_deps:
        report.add_error(
            "OpenAPI import requires backend dependencies in the current interpreter; missing: "
            + ", ".join(missing_import_deps)
        )
        return

    # Fallbacks are intentionally non-secret local values and are used only when
    # the caller has not supplied real settings. They keep import inspection from
    # failing before it reaches FastAPI schema generation.
    os.environ.setdefault("SECRET_KEY", "backend-core-check-secret")
    os.environ.setdefault("MASTER_KEY", "dGVzdC1tYXN0ZXIta2V5LWZvci10ZXN0aW5nLW9ubHk=")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SENTRY_ENABLED", "false")
    os.environ.setdefault("OUTGOING_WEBHOOKS_ENABLED", "false")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("REDIS_HOST", "localhost")

    sys.path.insert(0, str(backend_dir))
    previous_logging_disable = logging.root.manager.disable
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        logging.disable(logging.CRITICAL)
        with (
            contextlib.redirect_stdout(captured_stdout),
            contextlib.redirect_stderr(captured_stderr),
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter("always")
            from app.main import api  # type: ignore[import-not-found]

            schema = api.openapi()
    except Exception as exc:
        report.add_error(f"OpenAPI import failed: {type(exc).__name__}: {exc}")
        return
    finally:
        logging.disable(previous_logging_disable)
        try:
            sys.path.remove(str(backend_dir))
        except ValueError:
            pass

    suppressed_output = (captured_stdout.getvalue() + captured_stderr.getvalue()).strip().splitlines()
    if suppressed_output:
        report.add_warning(f"Suppressed {len(suppressed_output)} import-time log line(s) while building OpenAPI")

    paths = schema.get("paths", {})
    report.info["openapi_paths"] = len(paths)
    if len(paths) < 90:
        report.add_warning(f"Imported OpenAPI path count is lower than expected: {len(paths)}")
    else:
        report.add_ok(f"Imported OpenAPI schema contains {len(paths)} paths")

    repo_prefix = repo_root.as_posix().rstrip("/") + "/"
    warning_messages = [str(w.message).replace(repo_prefix, "") for w in caught]
    duplicate_warnings = [w for w in warning_messages if "Duplicate Operation ID" in w]
    if duplicate_warnings:
        report.add_warning("OpenAPI duplicate operation-id warnings observed: " + " | ".join(duplicate_warnings[:6]))
    report.info["openapi_warning_count"] = len(warning_messages)

    external_endpoints: set[str] = set()
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            tags = operation.get("tags", []) if isinstance(operation, dict) else []
            if any(str(tag).startswith("External:") for tag in tags):
                external_endpoints.add(f"{method.upper()} {path}")
    report.info["openapi_external_endpoints"] = len(external_endpoints)

    if docs_pages:
        missing_in_docs = sorted(external_endpoints - docs_pages)
        stale_in_docs = sorted(page for page in docs_pages if page.startswith(("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")) and page not in external_endpoints)
        if missing_in_docs:
            report.add_warning("External OpenAPI endpoints missing from docs/docs.json: " + "; ".join(missing_in_docs))
        else:
            report.add_ok("All imported External:* OpenAPI endpoints are present in docs/docs.json")
        if stale_in_docs:
            report.add_warning("docs/docs.json endpoint pages not present in imported External:* OpenAPI: " + "; ".join(stale_in_docs))


def build_report(args: argparse.Namespace) -> CheckReport:
    repo_root = find_repo_root(Path(args.repo_root) if args.repo_root else None)
    report = CheckReport(info={"repo_root": repo_root.as_posix()})
    if not (repo_root / "backend" / "app" / "main.py").exists():
        report.add_error("Repo root does not look like Open Wearables (missing backend/app/main.py)")
        return report

    check_required_files(repo_root, report)
    check_pyproject(repo_root, report)
    check_routes(repo_root, report)
    docs_pages = check_docs(repo_root, report)
    check_env_example(repo_root, report)
    check_tests(repo_root, report)
    if args.import_openapi:
        import_openapi(repo_root, docs_pages, report)
    return report


def print_text(report: CheckReport) -> None:
    print("backend-core checker")
    print(f"info: repo_root={report.info.get('repo_root')}")
    for key in sorted(k for k in report.info if k != "repo_root"):
        print(f"info: {key}={report.info[key]}")
    for item in report.ok:
        print(f"ok: {item}")
    for item in report.warnings:
        print(f"warning: {item}")
    for item in report.errors:
        print(f"error: {item}")
    status = "pass" if not report.errors else "fail"
    print(f"status: {status} ({len(report.errors)} errors, {len(report.warnings)} warnings)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only backend-core checker for Open Wearables.")
    parser.add_argument("--repo-root", help="Repository root to inspect. Defaults to walking up from cwd.")
    parser.add_argument(
        "--import-openapi",
        action="store_true",
        help="Import backend app and compare External:* OpenAPI endpoints with docs/docs.json. No network or writes.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are present.")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps({"ok": report.ok, "warnings": report.warnings, "errors": report.errors, "info": report.info}, indent=2, sort_keys=True))
    else:
        print_text(report)

    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

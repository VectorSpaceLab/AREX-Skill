#!/usr/bin/env python3
"""Safely inspect CubeStudio backend/frontend structure without imports.

This helper is intentionally static. It reads files under a provided
CubeStudio-like checkout and reports expected backend files, overlay presence,
AppBuilder registration hints, Celery task names, frontend package scripts, and
proxy targets. It never imports ``myapp``, never opens DB/Redis connections, and
never calls Docker, Kubernetes, npm, yarn, or long-running services.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DISTILLED_FACTS = {
    "verified_overlay_import_route_count": 684,
    "app_name": "myapp",
    "runtime_app_name": "CubeStudio",
    "runtime_config_sample": {
        "ENVIRONMENT": "dev",
        "PIPELINE_NAMESPACE": "pipeline",
        "NOTEBOOK_NAMESPACE": "jupyter",
        "SERVICE_NAMESPACE": "service",
        "REPOSITORY_ORG": "ccr.ccs.tencentyun.com/cube-studio/",
        "SERVICE_DOMAIN": "service.svc.cluster.local",
    },
}

EXPECTED_BACKEND_FILES: List[Tuple[str, str, bool]] = [
    ("myapp/__init__.py", "Flask app, config import, AppBuilder, request hooks", True),
    ("myapp/security.py", "MyappSecurityManager, user/role models, auth binding", True),
    ("myapp/cli.py", "Flask CLI init and seed catalogs", True),
    ("myapp/create_db.py", "MySQL database creation helper", True),
    ("myapp/check_tables.py", "required table sanity check", True),
    ("myapp/views/__init__.py", "imports view modules to trigger route registration", True),
    ("myapp/views/base.py", "shared FAB view helpers", True),
    ("myapp/views/baseApi.py", "shared REST API base", True),
    ("myapp/views/baseFormApi.py", "shared form API base", False),
    ("myapp/views/baseSQLA.py", "SQLA interface override", True),
    ("myapp/models/helpers.py", "model import/export helpers", True),
    ("myapp/tasks/celery_app.py", "global Celery app", True),
    ("myapp/tasks/schedules.py", "scheduled maintenance tasks", True),
    ("myapp/tasks/async_task.py", "asynchronous task handlers", True),
    ("myapp/tools/watch_workflow.py", "workflow Kubernetes watcher", True),
    ("myapp/tools/watch_service.py", "service pod watcher", True),
    ("myapp/tools/check_celery.py", "Celery backlog checker", False),
    ("myapp/tools/supervisord.conf", "watcher process supervisor config", False),
    ("myapp/config.py", "root config placeholder; expected to be empty", False),
    ("myapp/project.py", "root project placeholder; expected to be empty", False),
    ("install/docker/config.py", "Docker runtime config overlay", True),
    ("install/docker/project.py", "Docker project/auth hook overlay", True),
    ("install/docker/entrypoint.sh", "Docker backend entrypoint", True),
    ("install/docker/docker-compose.yml", "local stack composition and mount contract", True),
    ("install/kubernetes/cube/overlays/config/config.py", "Kubernetes config overlay", True),
    ("install/kubernetes/cube/overlays/config/project.py", "Kubernetes project/auth hook overlay", True),
    ("install/kubernetes/cube/overlays/config/entrypoint.sh", "Kubernetes entrypoint overlay", True),
]

FRONTEND_PACKAGES = [
    ("myapp/frontend", "main frontend SPA"),
    ("myapp/vision", "AI pipeline flow editor"),
    ("myapp/visionPlus", "data ETL pipeline flow editor"),
]

KEY_CONFIG_NAMES = [
    "APP_NAME",
    "AUTH_TYPE",
    "AUTH_USER_REGISTRATION_ROLE",
    "SQLALCHEMY_DATABASE_URI",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_PASSWORD",
    "CACHE_CONFIG",
    "CELERY_CONFIG",
    "PIPELINE_NAMESPACE",
    "NOTEBOOK_NAMESPACE",
    "SERVICE_NAMESPACE",
    "REPOSITORY_ORG",
    "PUSH_REPOSITORY_ORG",
    "SERVICE_DOMAIN",
    "CLUSTERS",
    "MODEL_URLS",
    "JWT_PASSWORD",
    "COOKIE_DOMAIN",
    "AUTH_PLATFORM_ACCESS",
]


def read_text(path: Path, max_chars: int = 1_500_000) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    if len(data) > max_chars:
        return data[:max_chars]
    return data


def file_record(root: Path, relative: str, role: str, critical: bool) -> Dict[str, Any]:
    path = root / relative
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else None
    return {
        "path": relative,
        "role": role,
        "critical": critical,
        "exists": exists,
        "bytes": size,
        "empty": bool(exists and path.is_file() and size == 0),
    }


def regex_find(pattern: str, text: str, flags: int = 0) -> List[str]:
    return [m.group(1) if m.groups() else m.group(0) for m in re.finditer(pattern, text, flags)]


def extract_view_imports(root: Path) -> List[str]:
    text = read_text(root / "myapp/views/__init__.py")
    imports: List[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*from\s+\.\s+import\s+([A-Za-z0-9_,\s]+)", line)
        if match:
            imports.extend(part.strip() for part in match.group(1).split(",") if part.strip())
    return imports


def extract_appbuilder_registrations(root: Path) -> List[Dict[str, str]]:
    registrations: List[Dict[str, str]] = []
    views_dir = root / "myapp/views"
    for path in sorted(views_dir.glob("*.py")) if views_dir.exists() else []:
        text = read_text(path)
        for match in re.finditer(
            r"appbuilder\.add_(api|view_no_menu|view|link)\(\s*([A-Za-z_][A-Za-z0-9_]*)",
            text,
        ):
            registrations.append(
                {
                    "file": str(path.relative_to(root)),
                    "kind": match.group(1),
                    "target": match.group(2),
                }
            )
    return registrations


def extract_celery_tasks(root: Path) -> Dict[str, List[str]]:
    tasks: Dict[str, List[str]] = {}
    tasks_dir = root / "myapp/tasks"
    for path in sorted(tasks_dir.glob("*.py")) if tasks_dir.exists() else []:
        text = read_text(path)
        names = regex_find(r"@celery_app\.task\(\s*name\s*=\s*['\"]([^'\"]+)", text)
        if names:
            tasks[str(path.relative_to(root))] = names
    return tasks


def extract_celery_schedule(root: Path) -> Dict[str, Any]:
    config = read_text(root / "install/docker/config.py")
    return {
        "beat_task_refs": sorted(set(regex_find(r"['\"]task['\"]\s*:\s*['\"]([^'\"]+)", config))),
        "annotation_task_refs": sorted(set(regex_find(r"['\"](task\.[^'\"]+)['\"]\s*:\s*\{", config))),
    }


def extract_config_presence(root: Path) -> Dict[str, bool]:
    config = read_text(root / "install/docker/config.py")
    presence: Dict[str, bool] = {}
    for name in KEY_CONFIG_NAMES:
        presence[name] = bool(re.search(rf"^\s*{re.escape(name)}\s*=", config, re.MULTILINE))
    return presence


def parse_package_json(root: Path, package_dir: str, role: str) -> Dict[str, Any]:
    pkg_path = root / package_dir / "package.json"
    proxy_path = root / package_dir / "src/setupProxy.js"
    record: Dict[str, Any] = {
        "directory": package_dir,
        "role": role,
        "package_json_exists": pkg_path.exists(),
        "setup_proxy_exists": proxy_path.exists(),
        "name": None,
        "version": None,
        "scripts": {},
        "proxy_targets": [],
        "proxy_paths_preview": [],
        "errors": [],
    }
    if pkg_path.exists():
        try:
            data = json.loads(read_text(pkg_path, max_chars=300_000))
            record["name"] = data.get("name")
            record["version"] = data.get("version")
            record["scripts"] = data.get("scripts", {})
        except Exception as exc:  # pragma: no cover - diagnostic path
            record["errors"].append(f"package.json parse error: {exc}")
    if proxy_path.exists():
        text = read_text(proxy_path, max_chars=300_000)
        record["proxy_targets"] = sorted(set(regex_find(r"target\s*:\s*['\"]([^'\"]+)", text)))
        patterns: List[str] = []
        for array_match in re.finditer(r"app\.use\(\s*\[(.*?)\]", text, re.DOTALL):
            patterns.extend(regex_find(r"['\"]([^'\"]+)['\"]", array_match.group(1)))
        # Also capture string-only app.use('/path', ...) patterns if they appear later.
        patterns.extend(regex_find(r"app\.use\(\s*['\"]([^'\"]+)['\"]", text))
        record["proxy_paths_preview"] = patterns[:40]
    return record


def build_preconditions(root: Path, files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    by_path = {item["path"]: item for item in files}
    root_config = by_path.get("myapp/config.py") or file_record(root, "myapp/config.py", "root config placeholder", False)
    root_project = by_path.get("myapp/project.py") or file_record(root, "myapp/project.py", "root project placeholder", False)
    docker_config = by_path.get("install/docker/config.py")
    docker_project = by_path.get("install/docker/project.py")
    security_text = read_text(root / "myapp/security.py", max_chars=300_000)
    init_text = read_text(root / "myapp/__init__.py", max_chars=300_000)

    preconditions: List[Dict[str, str]] = []
    preconditions.append(
        {
            "name": "runtime config overlay",
            "status": "ok" if docker_config and docker_config["exists"] else "missing",
            "detail": "Docker/Kubernetes config overlay must replace or provide myapp.config; checked-out root config is expected to be empty."
            if root_config.get("empty")
            else "Root config is not empty; verify whether this is intentional or a local mutation.",
        }
    )
    preconditions.append(
        {
            "name": "runtime project overlay",
            "status": "ok" if docker_project and docker_project["exists"] else "missing",
            "detail": "security.py imports Myauthdbview from myapp.project; the overlay must define it."
            if "Myauthdbview" in security_text
            else "Could not confirm Myauthdbview import in security.py.",
        }
    )
    preconditions.append(
        {
            "name": "myapp import side effects",
            "status": "info",
            "detail": "Importing myapp constructs SQLA, cache, Migrate, AppBuilder, request hooks, and views; this helper avoids that import.",
        }
    )
    preconditions.append(
        {
            "name": "route-count expectation",
            "status": "info",
            "detail": f"A prepared overlay import previously exposed {DISTILLED_FACTS['verified_overlay_import_route_count']} Flask routes; route counts far below that suggest overlay/import/registration gaps.",
        }
    )
    if 'os.environ.get("MYAPP_CONFIG", "myapp.config")' not in init_text and "MYAPP_CONFIG" not in init_text:
        preconditions.append(
            {
                "name": "config module discovery",
                "status": "warn",
                "detail": "Could not find MYAPP_CONFIG usage in myapp/__init__.py; checkout may differ from the distilled version.",
            }
        )
    return preconditions


def inspect(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    files = [file_record(root, rel, role, critical) for rel, role, critical in EXPECTED_BACKEND_FILES]
    missing_critical = [item["path"] for item in files if item["critical"] and not item["exists"]]
    frontend = [parse_package_json(root, rel, role) for rel, role in FRONTEND_PACKAGES]
    registrations = extract_appbuilder_registrations(root)
    celery_tasks = extract_celery_tasks(root)
    celery_schedule = extract_celery_schedule(root)
    config_presence = extract_config_presence(root)
    view_imports = extract_view_imports(root)

    warnings: List[str] = []
    if (root / "myapp/config.py").exists() and (root / "myapp/config.py").stat().st_size == 0:
        warnings.append("myapp/config.py is empty; this is expected only when runtime overlays provide the real config.")
    if (root / "myapp/project.py").exists() and (root / "myapp/project.py").stat().st_size == 0:
        warnings.append("myapp/project.py is empty; runtime overlay must define Myauthdbview and project hooks.")
    if missing_critical:
        warnings.append("Missing critical expected files: " + ", ".join(missing_critical))
    for pkg in frontend:
        warnings.extend(f"{pkg['directory']}: {err}" for err in pkg.get("errors", []))

    return {
        "root": str(root),
        "distilled_facts": DISTILLED_FACTS,
        "backend_files": files,
        "missing_critical_files": missing_critical,
        "route_and_import_preconditions": build_preconditions(root, files),
        "view_imports": view_imports,
        "appbuilder_registrations": {
            "count": len(registrations),
            "items": registrations,
        },
        "celery": {
            "tasks_by_file": celery_tasks,
            "schedule": celery_schedule,
        },
        "config_key_presence_in_docker_overlay": config_presence,
        "frontend_packages": frontend,
        "warnings": warnings,
    }


def print_human(report: Dict[str, Any]) -> None:
    print(f"CubeStudio static structure report: {report['root']}")
    print("\nBackend files:")
    for item in report["backend_files"]:
        status = "ok" if item["exists"] else "MISSING"
        if item["empty"]:
            status += " empty"
        mark = "required" if item["critical"] else "optional"
        print(f"  [{status:13}] {item['path']} ({mark}) - {item['role']}")

    print("\nRoute/import preconditions:")
    for item in report["route_and_import_preconditions"]:
        print(f"  [{item['status']}] {item['name']}: {item['detail']}")

    regs = report["appbuilder_registrations"]
    print(f"\nAppBuilder registrations found statically: {regs['count']}")
    for item in regs["items"][:30]:
        print(f"  {item['file']}: add_{item['kind']}({item['target']})")
    if regs["count"] > 30:
        print(f"  ... {regs['count'] - 30} more")

    print("\nView modules imported by myapp/views/__init__.py:")
    print("  " + ", ".join(report["view_imports"]) if report["view_imports"] else "  none found")

    print("\nCelery tasks:")
    for file, tasks in report["celery"]["tasks_by_file"].items():
        print(f"  {file}: {', '.join(tasks)}")
    schedule = report["celery"]["schedule"]
    if schedule["beat_task_refs"]:
        print("  beat refs: " + ", ".join(schedule["beat_task_refs"]))

    print("\nFrontend packages:")
    for pkg in report["frontend_packages"]:
        print(f"  {pkg['directory']} ({pkg['role']}):")
        print(f"    package: {pkg.get('name')} {pkg.get('version')}")
        scripts = pkg.get("scripts") or {}
        print("    scripts: " + (", ".join(f"{k}={v}" for k, v in scripts.items()) if scripts else "none"))
        print("    proxy targets: " + (", ".join(pkg.get("proxy_targets") or []) or "none"))
        if pkg.get("proxy_paths_preview"):
            print("    proxy paths: " + ", ".join(pkg["proxy_paths_preview"]))
        for err in pkg.get("errors", []):
            print(f"    ERROR: {err}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static CubeStudio backend/frontend structure inspector")
    parser.add_argument("root", nargs="?", default=".", help="CubeStudio checkout root to inspect (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a human-readable report")
    parser.add_argument("--strict", action="store_true", help="exit nonzero when critical expected files are missing or package JSON is malformed")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = inspect(Path(args.root))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_human(report)

    if args.strict and (report["missing_critical_files"] or any(pkg.get("errors") for pkg in report["frontend_packages"])):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

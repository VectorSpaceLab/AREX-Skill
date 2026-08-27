#!/usr/bin/env python3
"""Static SQL/init/version checks for Nexent deployment files.

This helper intentionally does not connect to Docker, Kubernetes, PostgreSQL, or
any network service. It inspects repository files only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Check:
    id: str
    severity: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


SQL_IDENTIFIER_RE = re.compile(r'"?([A-Za-z_][A-Za-z0-9_]*)"?')
VERSION_RE = re.compile(r"^v?\d+(?:\.\d+)*(?:[._-][A-Za-z0-9][A-Za-z0-9._-]*)?$|^latest$", re.IGNORECASE)
MIGRATION_NAME_RE = re.compile(r"^v(?P<version>\d+(?:\.\d+)*)(?:[._-].*)?\.sql$", re.IGNORECASE)
CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(?P<table>[^\(]+)\((?P<body>.*?)\);",
    re.IGNORECASE | re.DOTALL,
)
COMMENT_COLUMN_RE = re.compile(
    r"COMMENT\s+ON\s+COLUMN\s+(?P<target>.+?)\s+IS\s+",
    re.IGNORECASE | re.DOTALL,
)
ALTER_TABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?P<table>(?:\"?[A-Za-z_][A-Za-z0-9_]*\"?\.)?\"?[A-Za-z_][A-Za-z0-9_]*\"?)\s+(?P<body>.*?);",
    re.IGNORECASE | re.DOTALL,
)
ADD_COLUMN_RE = re.compile(
    r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?(?P<column>[A-Za-z_][A-Za-z0-9_]*)\"?",
    re.IGNORECASE,
)
DROP_COLUMN_RE = re.compile(
    r"DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?\"?(?P<column>[A-Za-z_][A-Za-z0-9_]*)\"?",
    re.IGNORECASE,
)


def add_check(
    checks: list[Check],
    check_id: str,
    severity: str,
    status: str,
    message: str,
    **details: Any,
) -> None:
    checks.append(Check(check_id, severity, status, message, details))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def trim_sample(items: Iterable[Any], limit: int = 25) -> dict[str, Any]:
    seq = list(items)
    return {"count": len(seq), "items": seq[:limit], "truncated": len(seq) > limit}


def normalize_identifier(value: str) -> str:
    value = value.strip().strip(";").strip()
    value = value.replace('"', "")
    value = value.split()[0] if value.split() else value
    if "." in value:
        value = value.split(".")[-1]
    return value.lower()


def split_table_column(target: str) -> tuple[str, str] | None:
    cleaned = target.strip().strip(";").replace('"', "")
    cleaned = re.sub(r"\s+", "", cleaned)
    parts = [part for part in cleaned.split(".") if part]
    if len(parts) < 2:
        return None
    return parts[-2].lower(), parts[-1].lower()


def strip_line_comments(sql: str) -> str:
    # Good enough for static deployment checks; SQL strings in this repo do not
    # rely on line-comment-like tokens for DDL structure.
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def parse_init_tables(sql: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for match in CREATE_TABLE_RE.finditer(sql):
        table = normalize_identifier(match.group("table"))
        columns: set[str] = set()
        for line in match.group("body").splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            first = line.split()[0].strip('"').lower()
            if first in {"constraint", "primary", "foreign", "unique", "check", "exclude"}:
                continue
            if re.fullmatch(r"[a-z_][a-z0-9_]*", first):
                columns.add(first)
        if table:
            tables[table] = columns
    return tables


def parse_comment_columns(sql: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for match in COMMENT_COLUMN_RE.finditer(sql):
        pair = split_table_column(match.group("target"))
        if pair:
            pairs.append(pair)
    return pairs


def parse_migration_column_ops(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sql = read_text(path)
    without_comments = strip_line_comments(sql)
    added: list[dict[str, str]] = []
    dropped: list[dict[str, str]] = []
    for alter in ALTER_TABLE_RE.finditer(without_comments):
        table = normalize_identifier(alter.group("table"))
        body = alter.group("body")
        for add in ADD_COLUMN_RE.finditer(body):
            added.append({"file": path.name, "table": table, "column": add.group("column").lower()})
        for drop in DROP_COLUMN_RE.finditer(body):
            dropped.append({"file": path.name, "table": table, "column": drop.group("column").lower()})
    return added, dropped


def version_tuple(value: str) -> tuple[int, ...] | None:
    value = value.strip()
    if value.lower() == "latest":
        return None
    match = re.search(r"\d+(?:\.\d+)*", value)
    if not match:
        return None
    return tuple(int(part) for part in match.group(0).split("."))


def compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    width = max(len(left), len(right))
    a = left + (0,) * (width - len(left))
    b = right + (0,) * (width - len(right))
    return (a > b) - (a < b)


def migration_version(path: Path) -> tuple[int, ...] | None:
    match = MIGRATION_NAME_RE.match(path.name)
    if not match:
        return None
    return tuple(int(part) for part in match.group("version").split("."))


def require_tokens(
    checks: list[Check],
    root: Path,
    check_id: str,
    path: Path,
    tokens: list[str],
    message: str,
) -> str:
    if not path.exists():
        add_check(checks, check_id, "error", "fail", f"Missing required file: {rel(path, root)}")
        return ""
    text = read_text(path)
    missing = [token for token in tokens if token not in text]
    if missing:
        add_check(
            checks,
            check_id,
            "error",
            "fail",
            message,
            file=rel(path, root),
            missing=missing,
        )
    else:
        add_check(checks, check_id, "info", "pass", message, file=rel(path, root))
    return text


def run_checks(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checks: list[Check] = []

    if not repo_root.exists() or not repo_root.is_dir():
        add_check(checks, "repo-root", "error", "fail", "Repository root does not exist or is not a directory", path=str(repo_root))
        return summarize(repo_root, checks, {})

    add_check(checks, "repo-root", "info", "pass", "Repository root is readable", path=str(repo_root))

    version_file = repo_root / "VERSION"
    root_version = ""
    root_version_tuple: tuple[int, ...] | None = None
    if not version_file.exists():
        add_check(checks, "version-file", "error", "fail", "Missing root VERSION file")
    else:
        root_version = read_text(version_file).splitlines()[0].strip() if read_text(version_file).splitlines() else ""
        root_version_tuple = version_tuple(root_version)
        if not root_version:
            add_check(checks, "version-file", "error", "fail", "Root VERSION file is empty", file="VERSION")
        elif not VERSION_RE.match(root_version):
            add_check(checks, "version-file", "warning", "warn", "Root VERSION has an unusual format", file="VERSION", version=root_version)
        else:
            add_check(checks, "version-file", "info", "pass", "Root VERSION is present", file="VERSION", version=root_version)

    backend_const = repo_root / "backend" / "consts" / "const.py"
    if backend_const.exists():
        const_text = read_text(backend_const)
        required = ["APP_VERSION", "_resolve_app_version", "VERSION", "/opt/nexent/VERSION"]
        missing = [token for token in required if token not in const_text]
        if missing:
            add_check(checks, "backend-version-resolution", "warning", "warn", "Backend version resolver may not follow deployment VERSION contract", file=rel(backend_const, repo_root), missing=missing)
        else:
            add_check(checks, "backend-version-resolution", "info", "pass", "Backend APP_VERSION resolves from deployment VERSION files", file=rel(backend_const, repo_root))
    else:
        add_check(checks, "backend-version-resolution", "warning", "warn", "Backend constants file not found; skipped APP_VERSION resolver check")

    init_sql = repo_root / "deploy" / "sql" / "init.sql"
    migrations_dir = repo_root / "deploy" / "sql" / "migrations"
    init_tables: dict[str, set[str]] = {}
    if not init_sql.exists():
        add_check(checks, "sql-init", "error", "fail", "Missing deployment init SQL", file=rel(init_sql, repo_root))
        init_text = ""
    else:
        init_text = read_text(init_sql)
        init_tables = parse_init_tables(init_text)
        if "CREATE SCHEMA IF NOT EXISTS nexent" not in init_text:
            add_check(checks, "sql-init", "warning", "warn", "Init SQL does not explicitly create nexent schema", file=rel(init_sql, repo_root))
        elif not init_tables:
            add_check(checks, "sql-init", "error", "fail", "Init SQL contains no CREATE TABLE IF NOT EXISTS blocks", file=rel(init_sql, repo_root))
        else:
            add_check(
                checks,
                "sql-init",
                "info",
                "pass",
                "Init SQL is present and parseable",
                file=rel(init_sql, repo_root),
                sha256=sha256(init_sql),
                table_count=len(init_tables),
                column_count=sum(len(cols) for cols in init_tables.values()),
            )

        missing_comments = []
        for table, column in parse_comment_columns(init_text):
            if table not in init_tables:
                missing_comments.append({"table": table, "column": column, "reason": "table_not_created_in_init"})
            elif column not in init_tables[table]:
                missing_comments.append({"table": table, "column": column, "reason": "column_not_created_in_init"})
        if missing_comments:
            add_check(
                checks,
                "init-column-comments",
                "error",
                "fail",
                "Init SQL comments columns that are not created in init SQL",
                **trim_sample(missing_comments),
            )
        else:
            add_check(checks, "init-column-comments", "info", "pass", "Init SQL column comments match parsed init columns")

    if not migrations_dir.exists() or not migrations_dir.is_dir():
        add_check(checks, "sql-migrations-dir", "error", "fail", "Missing SQL migrations directory", file=rel(migrations_dir, repo_root))
        migration_files: list[Path] = []
    else:
        migration_files = sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)
        if not migration_files:
            add_check(checks, "sql-migrations-dir", "error", "fail", "No SQL migration files found", dir=rel(migrations_dir, repo_root))
        else:
            add_check(checks, "sql-migrations-dir", "info", "pass", "SQL migration files are present", dir=rel(migrations_dir, repo_root), count=len(migration_files))

    bad_names = [path.name for path in migration_files if not MIGRATION_NAME_RE.match(path.name)]
    if bad_names:
        add_check(checks, "migration-filenames", "warning", "warn", "Some migration filenames do not match the versioned v*.sql convention", **trim_sample(bad_names))
    elif migration_files:
        add_check(checks, "migration-filenames", "info", "pass", "Migration filenames follow the versioned v*.sql convention")

    version_order = [path.name for path in sorted(migration_files, key=lambda p: migration_version(p) or (999999,))]
    lexical_order = [path.name for path in migration_files]
    if migration_files and version_order != lexical_order:
        add_check(
            checks,
            "migration-sort-order",
            "info",
            "info",
            "Lexical Python sort differs from migration version order; runner uses sort -V",
            lexical=lexical_order,
            version_order=version_order,
        )
    else:
        add_check(checks, "migration-sort-order", "info", "pass", "Migration filenames have stable version-aware order")

    if root_version_tuple is not None:
        ahead = []
        for path in migration_files:
            mv = migration_version(path)
            if mv is not None and compare_versions(mv, root_version_tuple) > 0:
                ahead.append({"file": path.name, "migration_version": ".".join(map(str, mv)), "root_version": root_version})
        if ahead:
            add_check(checks, "migration-version-vs-root-version", "info", "info", "Some migration files are versioned ahead of root VERSION; confirm release intent", **trim_sample(ahead))
        elif migration_files:
            add_check(checks, "migration-version-vs-root-version", "info", "pass", "No migration filename version is ahead of root VERSION", version=root_version)

    marker_hits = []
    all_added: list[dict[str, str]] = []
    all_dropped: list[dict[str, str]] = []
    for path in migration_files:
        text = read_text(path)
        if "nexent-migration-" in text:
            marker_hits.append(path.name)
        added, dropped = parse_migration_column_ops(path)
        all_added.extend(added)
        all_dropped.extend(dropped)
    if marker_hits:
        add_check(checks, "migration-marker-comments", "error", "fail", "Migration marker comments are not supported by current runner", **trim_sample(marker_hits))
    elif migration_files:
        add_check(checks, "migration-marker-comments", "info", "pass", "Migration files do not use unsupported marker comments")

    dropped_in_init = []
    for item in all_dropped:
        columns = init_tables.get(item["table"])
        if columns and item["column"] in columns:
            dropped_in_init.append(item)
    if dropped_in_init:
        add_check(checks, "dropped-columns-in-init", "info", "info", "Columns dropped by migrations still appear in init SQL; confirm this is intentional", **trim_sample(dropped_in_init))
    elif init_tables and all_dropped:
        add_check(checks, "dropped-columns-in-init", "info", "pass", "Parsed dropped migration columns are absent from init SQL")

    added_missing_from_init = []
    for item in all_added:
        columns = init_tables.get(item["table"])
        if columns is not None and item["column"] not in columns:
            added_missing_from_init.append(item)
    if added_missing_from_init:
        add_check(
            checks,
            "migration-adds-not-in-init",
            "info",
            "info",
            "Migrations add columns not present in init SQL; review when changing schema or following fresh-init sync rules",
            **trim_sample(added_missing_from_init, 40),
        )
    elif init_tables and all_added:
        add_check(checks, "migration-adds-not-in-init", "info", "pass", "Parsed migration-added columns are present in init SQL")

    legacy_init_candidates = [
        repo_root / "docker" / "init.sql",
        repo_root / "k8s" / "helm" / "nexent" / "charts" / "nexent-common" / "files" / "init.sql",
        repo_root / "deploy" / "k8s" / "helm" / "nexent" / "charts" / "nexent-common" / "files" / "init.sql",
    ]
    existing_legacy = [path for path in legacy_init_candidates if path.exists()]
    if existing_legacy and init_sql.exists():
        mismatches = [rel(path, repo_root) for path in existing_legacy if sha256(path) != sha256(init_sql)]
        if mismatches:
            add_check(checks, "legacy-init-sync", "warning", "warn", "Legacy fresh-deploy init SQL files differ from deploy/sql/init.sql", files=mismatches)
        else:
            add_check(checks, "legacy-init-sync", "info", "pass", "Legacy fresh-deploy init SQL files match deploy/sql/init.sql", files=[rel(p, repo_root) for p in existing_legacy])
    else:
        add_check(checks, "legacy-init-sync", "info", "pass", "No legacy Docker/K8s init SQL twins found; current layout uses deploy/sql/init.sql for both Docker and K8s")

    require_tokens(
        checks,
        repo_root,
        "sql-runner-contract",
        repo_root / "deploy" / "common" / "run-sql-migrations.sh",
        ["schema_migrations", "__init.sql", "sort -V", "app_version", "source_file", "pg_advisory_lock", "--migrate", "--wait"],
        "SQL runner includes filename/checksum/app-version migration contract",
    )
    require_tokens(
        checks,
        repo_root,
        "start-backend-sql-mode",
        repo_root / "deploy" / "common" / "start-backend.sh",
        ["NEXENT_SQL_STARTUP_MODE", "--migrate", "--wait", "off"],
        "Backend startup wrapper dispatches SQL migrate/wait/off modes",
    )

    docker_deploy = require_tokens(
        checks,
        repo_root,
        "docker-deploy-sql-checksum",
        repo_root / "deploy" / "docker" / "deploy.sh",
        ["NEXENT_SQL_FILES_CHECKSUM", "sql_files_checksum", "update_sql_files_checksum", "SQL_DIR"],
        "Docker deploy computes SQL file checksum for restart/rollout detection",
    )
    _ = docker_deploy
    for compose_name in ["docker-compose.yml", "docker-compose.prod.yml"]:
        require_tokens(
            checks,
            repo_root,
            f"docker-compose-sql-{compose_name}",
            repo_root / "deploy" / "docker" / "compose" / compose_name,
            ["/opt/nexent/sql", "NEXENT_SQL_STARTUP_MODE", "migrate", "wait", "NEXENT_SQL_FILES_CHECKSUM"],
            f"{compose_name} mounts SQL and declares SQL startup modes",
        )

    require_tokens(
        checks,
        repo_root,
        "k8s-deploy-sql-render",
        repo_root / "deploy" / "k8s" / "deploy.sh",
        ["SQL_INIT_FILE", "render_k8s_runtime_config_values", "sqlFiles", "rolloutChecksums", "migrations", "supabase"],
        "Kubernetes deploy renders SQL files and rollout checksums into Helm values",
    )
    require_tokens(
        checks,
        repo_root,
        "helm-sql-configmap",
        repo_root / "deploy" / "k8s" / "helm" / "nexent" / "charts" / "nexent-common" / "templates" / "init-sql-configmap.yaml",
        ["sqlFiles", "init.sql", "migrations-", "supabase-"],
        "Helm common chart renders SQL ConfigMap entries",
    )
    require_tokens(
        checks,
        repo_root,
        "helm-config-migrates",
        repo_root / "deploy" / "k8s" / "helm" / "nexent" / "charts" / "nexent-config" / "templates" / "deployment.yaml",
        ["NEXENT_SQL_STARTUP_MODE", "migrate", "/opt/nexent/sql", "checksum/nexent-sql"],
        "Kubernetes config service is the SQL migrator",
    )
    require_tokens(
        checks,
        repo_root,
        "helm-runtime-waits",
        repo_root / "deploy" / "k8s" / "helm" / "nexent" / "charts" / "nexent-runtime" / "templates" / "deployment.yaml",
        ["NEXENT_SQL_STARTUP_MODE", "wait", "/opt/nexent/sql", "checksum/nexent-sql"],
        "Kubernetes runtime waits for SQL migration target",
    )

    for dockerfile in [
        repo_root / "deploy" / "images" / "dockerfiles" / "main" / "Dockerfile",
        repo_root / "deploy" / "images" / "dockerfiles" / "data-process" / "Dockerfile",
    ]:
        require_tokens(
            checks,
            repo_root,
            f"dockerfile-version-{dockerfile.parent.name}",
            dockerfile,
            ["COPY VERSION /opt/nexent/VERSION", "run-sql-migrations.sh", "start-backend.sh"],
            f"{dockerfile.parent.name} image copies VERSION and SQL startup scripts",
        )

    test_files = [
        repo_root / "deploy" / "tests" / "test_sql_migrations.sh",
        repo_root / "deploy" / "tests" / "test_common.sh",
    ]
    missing_tests = [rel(path, repo_root) for path in test_files if not path.exists()]
    if missing_tests:
        add_check(checks, "deploy-tests", "warning", "warn", "Expected deploy static tests are missing", missing=missing_tests)
    else:
        add_check(checks, "deploy-tests", "info", "pass", "Expected deploy static tests are present", files=[rel(path, repo_root) for path in test_files])

    summary_details = {
        "rootVersion": root_version,
        "initTableCount": len(init_tables),
        "initColumnCount": sum(len(cols) for cols in init_tables.values()),
        "migrationFileCount": len(migration_files),
        "migrationAddedColumnCount": len(all_added),
        "migrationDroppedColumnCount": len(all_dropped),
    }
    return summarize(repo_root, checks, summary_details)


def summarize(repo_root: Path, checks: list[Check], details: dict[str, Any]) -> dict[str, Any]:
    errors = sum(1 for check in checks if check.severity == "error" and check.status == "fail")
    warnings = sum(1 for check in checks if check.severity == "warning" and check.status == "warn")
    status = "error" if errors else "warning" if warnings else "ok"
    return {
        "schemaVersion": 1,
        "status": status,
        "repoRoot": str(repo_root),
        "summary": {"errors": errors, "warnings": warnings, "checks": len(checks), **details},
        "checks": [asdict(check) for check in checks],
    }


def print_text(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print(f"Nexent SQL migration sync check: {result['status'].upper()}")
    print(
        "Summary: "
        f"{summary.get('errors', 0)} error(s), "
        f"{summary.get('warnings', 0)} warning(s), "
        f"{summary.get('checks', 0)} check(s)"
    )
    if summary.get("rootVersion"):
        print(f"Version: {summary['rootVersion']}")
    if "migrationFileCount" in summary:
        print(
            "SQL: "
            f"{summary.get('initTableCount', 0)} init table(s), "
            f"{summary.get('initColumnCount', 0)} init column(s), "
            f"{summary.get('migrationFileCount', 0)} migration file(s)"
        )
    print("")
    for check in result["checks"]:
        if check["status"] == "pass" and check["severity"] == "info":
            prefix = "PASS"
        elif check["status"] == "warn":
            prefix = "WARN"
        elif check["status"] == "fail":
            prefix = "FAIL"
        else:
            prefix = check["status"].upper()
        print(f"[{prefix}] {check['id']}: {check['message']}")
        details = check.get("details") or {}
        if check["status"] != "pass" and details:
            rendered = json.dumps(details, ensure_ascii=False, sort_keys=True)
            print(f"  details: {rendered}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run static Nexent deployment SQL/init/version checks without touching live services.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the Nexent repository root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_checks(Path(args.repo_root))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_text(result)
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe M-flow retrieval backend configuration probe.

This script validates provider names, optional dependency imports, and selected
configuration/environment keys. It is deterministic and safe by default: it does
not instantiate M-flow graph/vector/cache adapters, does not open network or
database connections, and does not mutate any store.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable

SECRET_MARKERS = ("KEY", "PASSWORD", "TOKEN", "SECRET")


@dataclass(frozen=True)
class ProviderSpec:
    kind: str
    name: str
    dependencies: tuple[str, ...] = ()
    extra: str = ""
    required_all: tuple[str, ...] = ()
    required_any: tuple[tuple[str, ...], ...] = ()
    optional_keys: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        kind="graph",
        name="kuzu",
        dependencies=("kuzu",),
        extra="bundled default dependency",
        optional_keys=("GRAPH_FILE_PATH", "GRAPH_FILENAME"),
        notes=("Embedded local graph default; no remote connection required.",),
    ),
    ProviderSpec(
        kind="graph",
        name="kuzu-remote",
        dependencies=("aiohttp", "kuzu"),
        extra="remote Kuzu support",
        required_all=("GRAPH_DATABASE_URL",),
        optional_keys=("GRAPH_DATABASE_USERNAME", "GRAPH_DATABASE_PASSWORD"),
        notes=("Requires a running remote Kuzu REST endpoint for live use.",),
    ),
    ProviderSpec(
        kind="graph",
        name="neo4j",
        dependencies=("neo4j",),
        extra="mflow-ai[neo4j]",
        required_all=("GRAPH_DATABASE_URL",),
        optional_keys=("GRAPH_DATABASE_NAME", "GRAPH_DATABASE_USERNAME", "GRAPH_DATABASE_PASSWORD"),
        notes=("The probe does not test Bolt reachability or credentials.",),
    ),
    ProviderSpec(
        kind="graph",
        name="neptune",
        dependencies=("langchain_aws",),
        extra="mflow-ai[neptune]",
        required_all=("GRAPH_DATABASE_URL",),
        notes=("Live use also requires AWS credentials and the expected endpoint prefix.",),
    ),
    ProviderSpec(
        kind="graph",
        name="neptune_analytics",
        dependencies=("langchain_aws",),
        extra="mflow-ai[neptune]",
        required_all=("GRAPH_DATABASE_URL",),
        notes=("Can pair with vector provider neptune_analytics.",),
    ),
    ProviderSpec(
        kind="vector",
        name="lancedb",
        dependencies=("lancedb",),
        extra="bundled default dependency",
        optional_keys=("VECTOR_DB_URL",),
        notes=("Local vector default; no remote service is contacted by this probe.",),
    ),
    ProviderSpec(
        kind="vector",
        name="pgvector",
        dependencies=("asyncpg", "pgvector", "psycopg2"),
        extra="mflow-ai[postgres] or mflow-ai[postgres-binary]",
        required_all=("DB_HOST", "DB_PORT", "DB_NAME", "DB_USERNAME", "DB_PASSWORD"),
        notes=("M-flow builds pgvector connection settings from relational DB config.",),
    ),
    ProviderSpec(
        kind="vector",
        name="chromadb",
        dependencies=("chromadb",),
        extra="mflow-ai[chromadb]",
        optional_keys=("VECTOR_DB_URL", "VECTOR_DB_KEY"),
        notes=("The adapter uses a Chroma HTTP client; live URL reachability is not checked.",),
    ),
    ProviderSpec(
        kind="vector",
        name="pinecone",
        dependencies=("pinecone",),
        extra="mflow-ai[pinecone]",
        required_any=(("VECTOR_DB_KEY", "PINECONE_API_KEY"),),
        optional_keys=("VECTOR_DB_NAME", "PINECONE_INDEX_NAME"),
        notes=("Index existence and API-key validity require a live Pinecone check.",),
    ),
    ProviderSpec(
        kind="vector",
        name="milvus",
        dependencies=("pymilvus",),
        extra="mflow-ai[milvus]",
        optional_keys=("VECTOR_DB_URL", "VECTOR_DB_KEY", "VECTOR_DB_NAME", "MILVUS_URI", "MILVUS_TOKEN"),
        notes=("Local Milvus defaults may be used by the adapter if no URI is supplied.",),
    ),
    ProviderSpec(
        kind="vector",
        name="neptune_analytics",
        dependencies=("langchain_aws",),
        extra="mflow-ai[neptune]",
        required_all=("VECTOR_DB_URL",),
        notes=("Live use requires AWS credentials and the expected Neptune Analytics endpoint prefix.",),
    ),
    ProviderSpec(
        kind="relational",
        name="sqlite",
        dependencies=("aiosqlite", "sqlalchemy"),
        extra="bundled default dependencies",
        optional_keys=("DB_PATH", "DB_NAME"),
        notes=("Default metadata/search-log backend.",),
    ),
    ProviderSpec(
        kind="relational",
        name="postgres",
        dependencies=("asyncpg", "pgvector", "psycopg2"),
        extra="mflow-ai[postgres] or mflow-ai[postgres-binary]",
        required_all=("DB_HOST", "DB_PORT", "DB_NAME", "DB_USERNAME", "DB_PASSWORD"),
        notes=("Use this for production metadata or pgvector-backed vector search.",),
    ),
    ProviderSpec(
        kind="relational",
        name="postgresql",
        dependencies=("asyncpg", "pgvector", "psycopg2"),
        extra="mflow-ai[postgres] or mflow-ai[postgres-binary]",
        required_all=("DB_HOST", "DB_PORT", "DB_NAME", "DB_USERNAME", "DB_PASSWORD"),
        notes=("Alias accepted by some SQLAlchemy paths; keep runtime config consistent.",),
    ),
    ProviderSpec(
        kind="cache",
        name="fs",
        dependencies=(),
        extra="bundled default",
        optional_keys=("CACHE_BACKEND",),
        notes=("Filesystem/local cache mode.",),
    ),
    ProviderSpec(
        kind="cache",
        name="redis",
        dependencies=("redis",),
        extra="mflow-ai[redis]",
        optional_keys=("CACHE_HOST", "CACHE_PORT", "CACHE_USERNAME", "CACHE_PASSWORD"),
        notes=("Live use requires a reachable Redis service.",),
    ),
)

DEFAULT_PROVIDER_BY_KIND = {
    "graph": "kuzu",
    "vector": "lancedb",
    "relational": "sqlite",
    "cache": "fs",
}

ENV_PROVIDER_KEY_BY_KIND = {
    "graph": "GRAPH_DATABASE_PROVIDER",
    "vector": "VECTOR_DB_PROVIDER",
    "relational": "DB_PROVIDER",
    "cache": "CACHE_BACKEND",
}


def _prefixed(key: str) -> str:
    return f"MFLOW_{key}"


def env_value(key: str) -> str | None:
    """Read MFLOW_KEY first, then bare KEY for compatibility."""
    pref = _prefixed(key)
    if pref in os.environ and os.environ[pref] != "":
        return os.environ[pref]
    if key in os.environ and os.environ[key] != "":
        return os.environ[key]
    return None


def env_presence(key: str) -> dict[str, Any]:
    value = env_value(key)
    source = None
    if _prefixed(key) in os.environ and os.environ[_prefixed(key)] != "":
        source = _prefixed(key)
    elif key in os.environ and os.environ[key] != "":
        source = key

    if value is None:
        shown = "<unset>"
    elif any(marker in key for marker in SECRET_MARKERS):
        shown = "<set:masked>"
    else:
        shown = "<set>"

    return {"key": key, "source": source, "present": value is not None, "value": shown}


def ensure_project_import_path() -> None:
    """Make a user-specified package source importable without printing any paths."""
    if importlib.util.find_spec("m_flow") is not None:
        return

    starts = [Path.cwd(), Path(__file__).resolve()]
    for start in starts:
        for parent in [start, *start.parents]:
            if (parent / "m_flow" / "__init__.py").exists():
                parent_str = str(parent)
                if parent_str not in sys.path:
                    sys.path.insert(0, parent_str)
                return


def module_available(module_name: str) -> bool:
    if module_name == "m_flow":
        ensure_project_import_path()
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def dependency_report(modules: Iterable[str]) -> list[dict[str, Any]]:
    return [{"module": m, "available": module_available(m)} for m in modules]


def package_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "m_flow_importable": module_available("m_flow"),
        "mflow_ai_distribution": None,
        "m_flow_module_version": None,
        "import_error": None,
    }
    try:
        report["mflow_ai_distribution"] = metadata.version("mflow-ai")
    except metadata.PackageNotFoundError:
        report["mflow_ai_distribution"] = None

    if report["m_flow_importable"]:
        try:
            module = importlib.import_module("m_flow")
            report["m_flow_module_version"] = getattr(module, "__version__", None)
        except Exception as exc:  # pragma: no cover - defensive in arbitrary envs
            report["import_error"] = f"{type(exc).__name__}: {exc}"
    return report


def provider_selected_for_kind(kind: str) -> str:
    key = ENV_PROVIDER_KEY_BY_KIND[kind]
    return (env_value(key) or DEFAULT_PROVIDER_BY_KIND[kind]).lower()


def matching_specs(kind: str, provider: str | None, all_known: bool) -> list[ProviderSpec]:
    if kind != "all":
        candidates = [spec for spec in PROVIDERS if spec.kind == kind]
    else:
        candidates = list(PROVIDERS)

    if provider:
        provider_l = provider.lower()
        return [spec for spec in candidates if spec.name.lower() == provider_l]

    if all_known:
        return candidates

    if kind == "all":
        selected: list[ProviderSpec] = []
        for k in ("graph", "vector", "relational", "cache"):
            name = provider_selected_for_kind(k)
            selected.extend([spec for spec in PROVIDERS if spec.kind == k and spec.name == name][:1])
        return selected

    selected_name = provider_selected_for_kind(kind)
    return [spec for spec in candidates if spec.name == selected_name]


def validate_required(spec: ProviderSpec) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for key in spec.required_all:
        if env_value(key) is None:
            missing.append(key)

    for group in spec.required_any:
        if not any(env_value(k) is not None for k in group):
            missing.append(" one of " + ", ".join(group))

    return not missing, missing


def spec_report(spec: ProviderSpec) -> dict[str, Any]:
    deps = dependency_report(spec.dependencies)
    deps_ok = all(item["available"] for item in deps)
    required_ok, missing = validate_required(spec)

    keys = list(dict.fromkeys((*spec.required_all, *[k for group in spec.required_any for k in group], *spec.optional_keys)))
    env = [env_presence(k) for k in keys]

    if deps_ok and required_ok:
        status = "ok"
    elif not deps_ok:
        status = "missing-import"
    else:
        status = "missing-config"

    return {
        "kind": spec.kind,
        "provider": spec.name,
        "status": status,
        "recognized": True,
        "safe_probe_only": True,
        "connectivity": "not-attempted",
        "extra_hint": spec.extra,
        "dependencies": deps,
        "required_config_ok": required_ok,
        "missing_required_config": missing,
        "environment": env,
        "notes": list(spec.notes),
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    specs = matching_specs(args.kind, args.provider, args.all_known)
    exit_code = 0

    if not specs:
        known = sorted({f"{s.kind}:{s.name}" for s in PROVIDERS if args.kind == "all" or s.kind == args.kind})
        report = {
            "safe_by_default": True,
            "error": f"unknown provider {args.provider!r} for kind {args.kind!r}",
            "known_providers": known,
        }
        return report, 2

    providers = [spec_report(spec) for spec in specs]
    if args.strict and any(p["status"] != "ok" for p in providers):
        exit_code = 1

    report = {
        "safe_by_default": True,
        "mutation": "none",
        "connectivity": "not-attempted",
        "selection": {
            "kind": args.kind,
            "provider": args.provider,
            "all_known": args.all_known,
        },
        "package": package_report(),
        "current_provider_env": {
            kind: {
                "provider_key": ENV_PROVIDER_KEY_BY_KIND[kind],
                "selected_or_default": provider_selected_for_kind(kind),
                "source": env_presence(ENV_PROVIDER_KEY_BY_KIND[kind])["source"],
            }
            for kind in ("graph", "vector", "relational", "cache")
        },
        "providers": providers,
    }
    return report, exit_code


def print_human(report: dict[str, Any]) -> None:
    if "error" in report:
        print(f"ERROR: {report['error']}", file=sys.stderr)
        print("Known providers:", file=sys.stderr)
        for item in report.get("known_providers", []):
            print(f"  - {item}", file=sys.stderr)
        return

    pkg = report.get("package", {})
    print("M-flow backend config probe (safe: no connections, no mutations)")
    print(f"m_flow importable: {pkg.get('m_flow_importable')}")
    print(f"mflow-ai distribution: {pkg.get('mflow_ai_distribution') or '<not found>'}")
    print(f"m_flow module version: {pkg.get('m_flow_module_version') or '<unknown>'}")
    if pkg.get("import_error"):
        print(f"m_flow import error: {pkg['import_error']}")

    print("\nCurrent selected/default providers:")
    for kind, info in report.get("current_provider_env", {}).items():
        source = info.get("source") or "default"
        print(f"  {kind}: {info.get('selected_or_default')} ({source})")

    print("\nProvider checks:")
    for provider in report.get("providers", []):
        print(f"\n[{provider['kind']}:{provider['provider']}] status={provider['status']}")
        if provider.get("extra_hint"):
            print(f"  extra/import hint: {provider['extra_hint']}")
        deps = provider.get("dependencies") or []
        if deps:
            for dep in deps:
                mark = "ok" if dep["available"] else "missing"
                print(f"  import {dep['module']}: {mark}")
        else:
            print("  imports: none required")
        if provider.get("missing_required_config"):
            print("  missing required config:")
            for key in provider["missing_required_config"]:
                print(f"    - {key}")
        env_rows = provider.get("environment") or []
        if env_rows:
            print("  config keys:")
            for row in env_rows:
                src = row["source"] or "unset"
                print(f"    - {row['key']}: {row['value']} ({src})")
        for note in provider.get("notes", []):
            print(f"  note: {note}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate M-flow retrieval backend provider names, optional imports, "
            "and config key visibility without connecting to services."
        )
    )
    parser.add_argument(
        "--kind",
        choices=("all", "graph", "vector", "relational", "cache"),
        default="all",
        help="Backend layer to inspect. Default: current/default provider for every layer.",
    )
    parser.add_argument(
        "--provider",
        help="Provider name to validate, for example neo4j, pgvector, lancedb, redis.",
    )
    parser.add_argument(
        "--all-known",
        action="store_true",
        help="Show all known providers for the selected kind instead of only current/default selections.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when selected providers have missing imports or required config.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report, exit_code = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

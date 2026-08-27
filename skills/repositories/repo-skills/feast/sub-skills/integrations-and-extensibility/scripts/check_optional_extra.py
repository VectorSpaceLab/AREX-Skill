#!/usr/bin/env python3
"""Preflight optional Feast extras by importing their Python modules.

This script never installs packages and never connects to backend services. It is
intended for generated Feast skills and can run outside the original Feast
checkout as long as the target Python environment is active.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True)
class ExtraCheck:
    extra: str
    modules: tuple[str, ...]
    note: str


CHECKS: dict[str, ExtraCheck] = {
    "aws": ExtraCheck("aws", ("boto3", "aiobotocore"), "AWS stores such as Redshift, DynamoDB, and Athena"),
    "azure": ExtraCheck("azure", ("azure.storage.blob", "azure.identity"), "Azure storage and SQL support"),
    "cassandra": ExtraCheck("cassandra", ("cassandra",), "Cassandra online store"),
    "clickhouse": ExtraCheck("clickhouse", ("clickhouse_connect",), "ClickHouse offline store"),
    "couchbase": ExtraCheck("couchbase", ("couchbase",), "Couchbase offline/online stores"),
    "dbt": ExtraCheck("dbt", ("dbt_artifacts_parser",), "dbt manifest import"),
    "duckdb": ExtraCheck("duckdb", ("ibis", "duckdb"), "DuckDB offline store through Ibis"),
    "elasticsearch": ExtraCheck("elasticsearch", ("elasticsearch",), "Elasticsearch online store"),
    "faiss": ExtraCheck("faiss", ("faiss",), "FAISS vector online store"),
    "flink": ExtraCheck("flink", ("pyflink",), "Flink compute engine"),
    "gcp": ExtraCheck("gcp", ("google.cloud.bigquery", "google.cloud.datastore", "google.cloud.bigtable"), "GCP BigQuery, Datastore, and Bigtable integrations"),
    "ge": ExtraCheck("ge", ("great_expectations",), "Great Expectations data quality monitoring"),
    "grpcio": ExtraCheck("grpcio", ("grpc", "grpc_reflection", "grpc_health"), "gRPC server/client support"),
    "hazelcast": ExtraCheck("hazelcast", ("hazelcast",), "Hazelcast online store"),
    "hbase": ExtraCheck("hbase", ("happybase",), "HBase online store"),
    "k8s": ExtraCheck("k8s", ("kubernetes",), "Kubernetes integrations"),
    "milvus": ExtraCheck("milvus", ("pymilvus",), "Milvus vector online store"),
    "mlflow": ExtraCheck("mlflow", ("mlflow",), "MLflow feature lineage integration"),
    "mongodb": ExtraCheck("mongodb", ("pymongo", "dns"), "MongoDB online/vector store"),
    "mysql": ExtraCheck("mysql", ("pymysql",), "MySQL online store"),
    "openlineage": ExtraCheck("openlineage", ("openlineage.client",), "OpenLineage event emission"),
    "oracle": ExtraCheck("oracle", ("ibis",), "Oracle offline store through Ibis"),
    "postgres": ExtraCheck("postgres", ("psycopg",), "PostgreSQL online/offline stores"),
    "postgres-c": ExtraCheck("postgres-c", ("psycopg",), "PostgreSQL psycopg C-extension variant"),
    "qdrant": ExtraCheck("qdrant", ("qdrant_client",), "Qdrant vector online store"),
    "rag": ExtraCheck("rag", ("transformers", "datasets", "sentence_transformers"), "RAG helper dependencies"),
    "ray": ExtraCheck("ray", ("ray", "datasets"), "Ray offline store and compute engine"),
    "redis": ExtraCheck("redis", ("redis", "redis.asyncio"), "Redis online store"),
    "singlestore": ExtraCheck("singlestore", ("singlestoredb",), "SingleStore online store"),
    "snowflake": ExtraCheck("snowflake", ("snowflake.connector",), "Snowflake offline/online store and compute engine"),
    "spark": ExtraCheck("spark", ("pyspark",), "Spark offline store and compute engine"),
    "sqlite_vec": ExtraCheck("sqlite_vec", ("sqlite_vec",), "SQLite vector extension"),
    "trino": ExtraCheck("trino", ("trino", "regex"), "Trino offline store"),
}

ALIASES: dict[str, tuple[str, ...]] = {
    "snowflake-redis": ("snowflake", "redis"),
    "ml-platform": ("mlflow", "openlineage", "ge"),
    "distributed-compute": ("ray", "spark", "flink", "snowflake"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check imports for selected Feast optional extras without installing packages or connecting to services.",
    )
    parser.add_argument(
        "--extras",
        nargs="+",
        default=[],
        help="Feast extras or aliases to check. Examples: redis snowflake dbt mlflow openlineage ge. Aliases: snowflake-redis, ml-platform, distributed-compute.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List known extras and aliases, then exit.",
    )
    parser.add_argument(
        "--check-feast",
        action="store_true",
        help="Also verify that the feast package is importable and print its installed version when available.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text output.",
    )
    return parser.parse_args()


def expand_extras(extras: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for extra in extras:
        normalized = extra.strip()
        if not normalized:
            continue
        for item in ALIASES.get(normalized, (normalized,)):
            if item not in expanded:
                expanded.append(item)
    return expanded


def import_status(module_name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report any import-time dependency/config error.
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def feast_status() -> dict[str, object]:
    ok, error = import_status("feast")
    version = None
    if ok:
        try:
            version = metadata.version("feast")
        except metadata.PackageNotFoundError:
            version = getattr(importlib.import_module("feast"), "__version__", None)
    return {"name": "feast", "ok": ok, "version": version, "error": error}


def check_extra(extra: str) -> dict[str, object]:
    check = CHECKS.get(extra)
    if check is None:
        return {
            "extra": extra,
            "known": False,
            "ok": False,
            "modules": [],
            "missing": [],
            "note": "Unknown extra. Use --list to see supported names.",
            "suggestion": None,
        }

    module_results = []
    missing = []
    for module_name in check.modules:
        ok, error = import_status(module_name)
        module_results.append({"module": module_name, "ok": ok, "error": error})
        if not ok:
            missing.append(module_name)

    return {
        "extra": extra,
        "known": True,
        "ok": not missing,
        "modules": module_results,
        "missing": missing,
        "note": check.note,
        "suggestion": None if not missing else f"pip install 'feast[{extra}]'",
    }


def print_list() -> None:
    print("Known Feast extras:")
    for name in sorted(CHECKS):
        print(f"  {name:16} {CHECKS[name].note}")
    print("\nAliases:")
    for name, extras in sorted(ALIASES.items()):
        print(f"  {name:16} {' '.join(extras)}")


def print_text(results: list[dict[str, object]], feast: dict[str, object] | None) -> None:
    if feast is not None:
        if feast["ok"]:
            version = feast.get("version") or "unknown version"
            print(f"OK      feast ({version})")
        else:
            print(f"MISSING feast: {feast['error']}")
            print("        Suggestion: install Feast in this Python environment, for example pip install feast")

    for result in results:
        extra = result["extra"]
        if not result["known"]:
            print(f"UNKNOWN {extra}: {result['note']}")
            continue

        status = "OK" if result["ok"] else "MISSING"
        print(f"{status:7} {extra}: {result['note']}")
        for module_result in result["modules"]:
            module_status = "ok" if module_result["ok"] else "missing"
            print(f"        {module_status:7} import {module_result['module']}")
            if module_result["error"]:
                print(f"                {module_result['error']}")
        if result["suggestion"]:
            print(f"        Suggestion: {result['suggestion']}")


def main() -> int:
    args = parse_args()

    if args.list:
        if args.json:
            print(json.dumps({"extras": sorted(CHECKS), "aliases": ALIASES}, indent=2, sort_keys=True))
        else:
            print_list()
        return 0

    extras = expand_extras(args.extras)
    if not extras and not args.check_feast:
        print("No extras selected. Use --extras redis snowflake, --check-feast, or --list.", file=sys.stderr)
        return 2

    results = [check_extra(extra) for extra in extras]
    feast = feast_status() if args.check_feast else None
    overall_ok = all(result["ok"] for result in results) and (feast is None or bool(feast["ok"]))

    if args.json:
        print(json.dumps({"ok": overall_ok, "feast": feast, "results": results}, indent=2, sort_keys=True))
    else:
        print_text(results, feast)

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

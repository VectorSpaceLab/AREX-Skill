#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Summarize Airflow Helm values without Helm or cluster access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on minimal hosts
    yaml = None

SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "fernet",
    "jwt",
    "key",
    "connection",
    "brokerurl",
)

PLAIN_SECRET_PATHS = (
    "data.metadataConnection.pass",
    "data.brokerUrl",
    "fernetKey",
    "apiSecretKey",
    "jwtSecret",
    "redis.password",
    "dags.gitSync.sshKey",
    "elasticsearch.connection",
    "opensearch.connection",
)

COMPONENT_PATHS = {
    "api server": "apiServer.enabled",
    "scheduler": "scheduler.enabled",
    "Dag processor": "dagProcessor.enabled",
    "triggerer": "triggerer.enabled",
    "Celery workers": "workers.celery.enableDefault",
    "Redis": "redis.enabled",
    "PgBouncer": "pgbouncer.enabled",
    "bundled PostgreSQL": "postgresql.enabled",
    "Flower": "flower.enabled",
    "StatsD": "statsd.enabled",
    "OpenTelemetry collector": "otelCollector.enabled",
    "Dag persistence": "dags.persistence.enabled",
    "Dag git-sync": "dags.gitSync.enabled",
    "logs persistence": "logs.persistence.enabled",
    "worker KEDA": "workers.celery.keda.enabled",
    "worker HPA": "workers.celery.hpa.enabled",
    "API server HPA": "apiServer.hpa.enabled",
    "triggerer KEDA": "triggerer.keda.enabled",
    "Elasticsearch logging": "elasticsearch.enabled",
    "OpenSearch logging": "opensearch.enabled",
}

DEFAULT_TRUE_PATHS = {
    "apiServer.enabled",
    "scheduler.enabled",
    "dagProcessor.enabled",
    "triggerer.enabled",
    "workers.celery.enableDefault",
    "redis.enabled",
    "postgresql.enabled",
}


def get_path(values: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = values
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def has_path(values: dict[str, Any], dotted_path: str) -> bool:
    sentinel = object()
    return get_path(values, dotted_path, sentinel) is not sentinel


def is_enabled(values: dict[str, Any], dotted_path: str) -> bool:
    default = True if dotted_path in DEFAULT_TRUE_PATHS else False
    return bool(get_path(values, dotted_path, default))


def as_bool_text(value: bool) -> str:
    return "enabled" if value else "disabled"


def flatten_paths(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        paths: list[tuple[str, Any]] = []
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(flatten_paths(item, next_prefix))
        return paths
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            next_prefix = f"{prefix}[{index}]"
            paths.extend(flatten_paths(item, next_prefix))
        return paths
    return [(prefix, value)]


def looks_sensitive(path: str, value: Any) -> bool:
    normalized = path.lower().replace("_", "")
    if not any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
        return False
    if value in (None, "", "~"):
        return False
    if isinstance(value, (bool, int, float)):
        return False
    return True


def collect_inline_secret_paths(values: dict[str, Any]) -> list[str]:
    findings = []
    for path in PLAIN_SECRET_PATHS:
        value = get_path(values, path)
        if value not in (None, "", "~"):
            findings.append(path)
    for path, value in flatten_paths(values):
        if looks_sensitive(path, value) and path not in findings:
            if path.endswith("SecretName") or path.endswith("secretName") or path.endswith("SecretKey"):
                continue
            findings.append(path)
    return sorted(findings)


def collect_enabled_components(values: dict[str, Any]) -> list[str]:
    components = []
    for label, path in COMPONENT_PATHS.items():
        enabled = is_enabled(values, path)
        if enabled:
            components.append(label)
    return components


def collect_images(values: dict[str, Any]) -> list[str]:
    default_repo = get_path(values, "defaultAirflowRepository", "apache/airflow")
    default_tag = get_path(values, "defaultAirflowTag", "<chart-default>")
    airflow_repo = get_path(values, "images.airflow.repository") or default_repo
    airflow_tag = get_path(values, "images.airflow.tag") or default_tag
    airflow_digest = get_path(values, "images.airflow.digest") or get_path(values, "defaultAirflowDigest")
    pod_template_repo = get_path(values, "images.pod_template.repository") or default_repo
    pod_template_tag = get_path(values, "images.pod_template.tag") or default_tag
    pull_policy = get_path(values, "images.airflow.pullPolicy", "IfNotPresent")

    image_lines = [
        f"default Airflow image: {default_repo}:{default_tag}",
        f"Airflow workload image: {airflow_repo}:{airflow_tag}",
        f"Airflow pull policy: {pull_policy}",
        f"KubernetesExecutor pod template image: {pod_template_repo}:{pod_template_tag}",
    ]
    if airflow_digest:
        image_lines.append("Airflow digest is set and takes precedence over tag")
    return image_lines


def collect_warnings(values: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    executor = str(get_path(values, "executor", "CeleryExecutor"))

    if is_enabled(values, "postgresql.enabled"):
        warnings.append(
            "bundled PostgreSQL is enabled; use an external database for production-like deployments"
        )

    if "CeleryExecutor" in executor:
        redis_enabled = is_enabled(values, "redis.enabled")
        has_broker_secret = has_path(values, "data.brokerUrlSecretName") and bool(
            get_path(values, "data.brokerUrlSecretName")
        )
        has_broker_url = has_path(values, "data.brokerUrl") and bool(get_path(values, "data.brokerUrl"))
        if not redis_enabled and not (has_broker_secret or has_broker_url):
            warnings.append("Celery executor has Redis disabled but no external broker URL or broker Secret")

    if is_enabled(values, "workers.celery.keda.enabled") and is_enabled(values, "workers.celery.hpa.enabled"):
        warnings.append("worker KEDA and worker HPA are both enabled; they should not scale the same target")

    if is_enabled(values, "elasticsearch.enabled") and is_enabled(values, "opensearch.enabled"):
        warnings.append(
            "Elasticsearch and OpenSearch logging are both enabled; choose one remote log backend"
        )

    if is_enabled(values, "dags.gitSync.enabled") and is_enabled(values, "dags.persistence.enabled"):
        warnings.append(
            "git-sync and Dag persistence are both enabled; validate shared filesystem consistency "
            "and POSIX behavior"
        )

    if is_enabled(values, "logs.persistence.enabled"):
        access_mode = get_path(values, "logs.persistence.accessMode") or get_path(
            values, "logs.persistence.accessModes"
        )
        if access_mode is None:
            warnings.append(
                "logs persistence is enabled; confirm storage supports the required shared write pattern"
            )

    if get_path(values, "images.airflow.pullPolicy") == "Always":
        warnings.append("Airflow image pullPolicy is Always; confirm this is intentional outside development")

    if has_path(values, "webserver"):
        warnings.append("legacy webserver values are present; Airflow 3 chart values should use apiServer")

    if get_path(values, "airflowVersion") and str(get_path(values, "airflowVersion")) < "3.1.0":
        warnings.append(
            "airflowVersion appears older than 3.1.0, which is below this chart generation's "
            "support floor"
        )

    for path in collect_inline_secret_paths(values):
        warnings.append(
            f"possible inline sensitive value at {path}; prefer an existing Kubernetes Secret reference"
        )

    return warnings


def print_section(title: str, lines: list[str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not lines:
        print("(none)")
        return
    for line in lines:
        print(f"- {line}")


def load_values(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit(
            "PyYAML is required to read Helm values YAML. Install pyyaml or run in an environment "
            "that includes it."
        )
    with path.open(encoding="utf-8") as values_file:
        loaded = yaml.safe_load(values_file) or {}
    if not isinstance(loaded, dict):
        raise SystemExit("Expected a YAML mapping at the root of the values file.")
    return loaded


def build_summary(values: dict[str, Any]) -> dict[str, Any]:
    executor = get_path(values, "executor", "CeleryExecutor")
    return {
        "executor": executor,
        "airflow_version": get_path(values, "airflowVersion", "<chart-default>"),
        "enabled_components": collect_enabled_components(values),
        "images": collect_images(values),
        "dag_delivery": {
            "persistence": as_bool_text(is_enabled(values, "dags.persistence.enabled")),
            "git_sync": as_bool_text(is_enabled(values, "dags.gitSync.enabled")),
            "git_repo_configured": bool(get_path(values, "dags.gitSync.repo")),
            "git_sub_path": get_path(values, "dags.gitSync.subPath"),
            "dag_bundles_configured": has_path(values, "dagProcessor.dagBundleConfigList"),
        },
        "database": {
            "bundled_postgresql": as_bool_text(is_enabled(values, "postgresql.enabled")),
            "metadata_secret_name_set": bool(get_path(values, "data.metadataSecretName")),
            "pgbouncer": as_bool_text(is_enabled(values, "pgbouncer.enabled")),
        },
        "logging": {
            "logs_persistence": as_bool_text(is_enabled(values, "logs.persistence.enabled")),
            "elasticsearch": as_bool_text(is_enabled(values, "elasticsearch.enabled")),
            "opensearch": as_bool_text(is_enabled(values, "opensearch.enabled")),
        },
        "scaling": {
            "worker_keda": as_bool_text(is_enabled(values, "workers.celery.keda.enabled")),
            "worker_hpa": as_bool_text(is_enabled(values, "workers.celery.hpa.enabled")),
            "api_server_hpa": as_bool_text(is_enabled(values, "apiServer.hpa.enabled")),
            "triggerer_keda": as_bool_text(is_enabled(values, "triggerer.keda.enabled")),
        },
        "warnings": collect_warnings(values),
    }


def print_text_summary(summary: dict[str, Any]) -> None:
    print("Airflow Helm values summary")
    print("===========================")
    print(f"Executor: {summary['executor']}")
    print(f"Airflow version value: {summary['airflow_version']}")
    print_section("Enabled components", summary["enabled_components"])
    print_section("Images", summary["images"])

    print_section(
        "Dag delivery",
        [f"{key.replace('_', ' ')}: {value}" for key, value in summary["dag_delivery"].items()],
    )
    print_section(
        "Database", [f"{key.replace('_', ' ')}: {value}" for key, value in summary["database"].items()]
    )
    print_section(
        "Logging", [f"{key.replace('_', ' ')}: {value}" for key, value in summary["logging"].items()]
    )
    print_section(
        "Scaling", [f"{key.replace('_', ' ')}: {value}" for key, value in summary["scaling"].items()]
    )
    print_section("Warnings", summary["warnings"])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("values_file", type=Path, help="Path to an Airflow Helm values YAML file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    values = load_values(args.values_file)
    summary = build_summary(values)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text_summary(summary)
    return 1 if summary["warnings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

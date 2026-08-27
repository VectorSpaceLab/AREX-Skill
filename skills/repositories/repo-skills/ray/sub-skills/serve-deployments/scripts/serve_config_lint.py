#!/usr/bin/env python3
"""Lint Ray Serve YAML config files without contacting a Ray cluster.

This helper intentionally performs structural checks only. It does not import the
user application and does not call Ray or Serve APIs, so it is safe to run during
code review and CI preflight.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency message path
    raise SystemExit(
        "PyYAML is required to lint Serve config files. Install ray[serve] or pyyaml."
    ) from exc

REMOTE_URI_SCHEMES = {
    "s3",
    "gs",
    "gcs",
    "http",
    "https",
}

LIGHTWEIGHT_FIELDS = {
    "num_replicas",
    "autoscaling_config",
    "user_config",
    "max_ongoing_requests",
    "graceful_shutdown_timeout_s",
    "graceful_shutdown_wait_loop_s",
    "health_check_period_s",
    "health_check_timeout_s",
}

CODE_UPDATE_FIELDS = {
    "ray_actor_options",
    "placement_group_bundles",
    "placement_group_strategy",
    "import_path",
    "runtime_env",
}

ROUTE_PREFIX_RE = re.compile(r"^/($|[^{}]*[^/{}]$)")


class Finding:
    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def render(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


def is_mapping(value: Any) -> bool:
    return isinstance(value, dict)


def is_remote_uri(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in REMOTE_URI_SCHEMES and bool(parsed.netloc or parsed.path)


def is_jsonable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def check_route_prefix(route_prefix: Any) -> str | None:
    if route_prefix is None:
        return None
    if not isinstance(route_prefix, str):
        return "route_prefix must be a string or null"
    if not route_prefix.startswith("/"):
        return 'route_prefix must start with "/"'
    if len(route_prefix) > 1 and route_prefix.endswith("/"):
        return 'route_prefix cannot end with "/" unless it is exactly "/"'
    if "{" in route_prefix or "}" in route_prefix:
        return "route_prefix cannot contain wildcards"
    if not ROUTE_PREFIX_RE.match(route_prefix):
        return "route_prefix has an invalid format"
    return None


def add_jsonability_warning(findings: list[Finding], path: str, value: Any) -> None:
    if value is not None and not is_jsonable(value):
        findings.append(
            Finding("WARN", path, "value may not be JSON-serializable for Serve")
        )


def lint_runtime_env(findings: list[Finding], runtime_env: Any, path: str) -> None:
    if runtime_env is None:
        return
    if not is_mapping(runtime_env):
        findings.append(Finding("ERROR", path, "runtime_env must be a mapping"))
        return

    working_dir = runtime_env.get("working_dir")
    if working_dir is not None and not is_remote_uri(working_dir):
        findings.append(
            Finding(
                "ERROR",
                f"{path}.working_dir",
                "Serve config runtime_env.working_dir must be a remote URI",
            )
        )

    py_modules = runtime_env.get("py_modules")
    if py_modules is not None:
        if not isinstance(py_modules, list):
            findings.append(
                Finding("ERROR", f"{path}.py_modules", "py_modules must be a list")
            )
        else:
            for index, uri in enumerate(py_modules):
                if not is_remote_uri(uri):
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{path}.py_modules[{index}]",
                            "Serve config runtime_env.py_modules entries must be remote URIs",
                        )
                    )

    add_jsonability_warning(findings, path, runtime_env)


def lint_deployment(findings: list[Finding], deployment: Any, path: str) -> None:
    if not is_mapping(deployment):
        findings.append(Finding("ERROR", path, "deployment entry must be a mapping"))
        return

    name = deployment.get("name")
    if not isinstance(name, str) or not name:
        findings.append(Finding("ERROR", f"{path}.name", "deployment name is required"))

    num_replicas = deployment.get("num_replicas")
    autoscaling_config = deployment.get("autoscaling_config")
    if isinstance(num_replicas, int) and autoscaling_config not in (None, {}):
        findings.append(
            Finding(
                "ERROR",
                path,
                "fixed integer num_replicas cannot be combined with autoscaling_config",
            )
        )
    if num_replicas not in (None, "auto") and not isinstance(num_replicas, int):
        findings.append(
            Finding(
                "ERROR",
                f"{path}.num_replicas",
                'num_replicas must be an integer, "auto", null, or omitted',
            )
        )

    ray_actor_options = deployment.get("ray_actor_options")
    if ray_actor_options is not None:
        if not is_mapping(ray_actor_options):
            findings.append(
                Finding("ERROR", f"{path}.ray_actor_options", "must be a mapping")
            )
        else:
            lint_runtime_env(
                findings,
                ray_actor_options.get("runtime_env"),
                f"{path}.ray_actor_options.runtime_env",
            )

    for json_field in (
        "user_config",
        "logging_config",
        "request_router_config",
        "autoscaling_config",
    ):
        if json_field in deployment:
            add_jsonability_warning(
                findings, f"{path}.{json_field}", deployment.get(json_field)
            )

    touched_lightweight = sorted(LIGHTWEIGHT_FIELDS.intersection(deployment))
    touched_code = sorted(CODE_UPDATE_FIELDS.intersection(deployment))
    if touched_lightweight:
        findings.append(
            Finding(
                "INFO",
                path,
                "lightweight deployment fields present: " + ", ".join(touched_lightweight),
            )
        )
    if touched_code:
        findings.append(
            Finding(
                "INFO",
                path,
                "code-update deployment fields present: " + ", ".join(touched_code),
            )
        )


def lint_application(findings: list[Finding], app: Any, path: str) -> tuple[str | None, str | None]:
    if not is_mapping(app):
        findings.append(Finding("ERROR", path, "application entry must be a mapping"))
        return None, None

    app_name = app.get("name")
    if app_name is not None and (not isinstance(app_name, str) or not app_name):
        findings.append(Finding("ERROR", f"{path}.name", "app name must be a non-empty string"))
        app_name = None

    import_path = app.get("import_path")
    if not isinstance(import_path, str) or not import_path:
        findings.append(Finding("ERROR", f"{path}.import_path", "import_path is required"))

    route_prefix = app.get("route_prefix")
    route_error = check_route_prefix(route_prefix)
    if route_error:
        findings.append(Finding("ERROR", f"{path}.route_prefix", route_error))
        route_prefix = None

    lint_runtime_env(findings, app.get("runtime_env"), f"{path}.runtime_env")

    if "args" in app:
        add_jsonability_warning(findings, f"{path}.args", app.get("args"))

    deployments = app.get("deployments", [])
    has_builtin_autoscaling = False
    if deployments is not None:
        if not isinstance(deployments, list):
            findings.append(Finding("ERROR", f"{path}.deployments", "must be a list"))
        else:
            deployment_names: set[str] = set()
            for index, deployment in enumerate(deployments):
                deployment_path = f"{path}.deployments[{index}]"
                if is_mapping(deployment):
                    deployment_name = deployment.get("name")
                    if isinstance(deployment_name, str):
                        if deployment_name in deployment_names:
                            findings.append(
                                Finding(
                                    "ERROR",
                                    f"{deployment_path}.name",
                                    "duplicate deployment override name in one app",
                                )
                            )
                        deployment_names.add(deployment_name)
                    if deployment.get("autoscaling_config") not in (None, {}):
                        has_builtin_autoscaling = True
                lint_deployment(findings, deployment, deployment_path)

    if app.get("external_scaler_enabled") is True and has_builtin_autoscaling:
        findings.append(
            Finding(
                "ERROR",
                path,
                "external_scaler_enabled cannot be combined with deployment autoscaling_config",
            )
        )

    touched_code = sorted(CODE_UPDATE_FIELDS.intersection(app))
    if touched_code:
        findings.append(
            Finding(
                "INFO",
                path,
                "code-update application fields present: " + ", ".join(touched_code),
            )
        )

    return app_name, route_prefix if isinstance(route_prefix, str) else None


def lint_config(config: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not is_mapping(config):
        return [Finding("ERROR", "$", "Serve config must be a YAML mapping")]

    applications = config.get("applications")
    if not isinstance(applications, list) or not applications:
        findings.append(
            Finding("ERROR", "$.applications", "applications must be a non-empty list")
        )
        return findings

    app_names: set[str] = set()
    route_prefixes: set[str] = set()
    for index, app in enumerate(applications):
        app_name, route_prefix = lint_application(findings, app, f"$.applications[{index}]")
        if app_name:
            if app_name in app_names:
                findings.append(
                    Finding("ERROR", f"$.applications[{index}].name", "duplicate app name")
                )
            app_names.add(app_name)
        if route_prefix:
            if route_prefix in route_prefixes:
                findings.append(
                    Finding(
                        "ERROR",
                        f"$.applications[{index}].route_prefix",
                        "duplicate route_prefix",
                    )
                )
            route_prefixes.add(route_prefix)

    if "http_options" in config and not is_mapping(config["http_options"]):
        findings.append(Finding("ERROR", "$.http_options", "must be a mapping"))
    if "grpc_options" in config and not is_mapping(config["grpc_options"]):
        findings.append(Finding("ERROR", "$.grpc_options", "must be a mapping"))
    if "logging_config" in config:
        add_jsonability_warning(findings, "$.logging_config", config["logging_config"])

    proxy_location = config.get("proxy_location")
    if proxy_location is not None and proxy_location not in {"EveryNode", "HeadOnly", "Disabled"}:
        findings.append(
            Finding(
                "ERROR",
                "$.proxy_location",
                "must be one of EveryNode, HeadOnly, or Disabled",
            )
        )

    return findings


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a Ray Serve YAML config without importing apps or contacting a cluster."
    )
    parser.add_argument("config", type=Path, help="Path to a Serve YAML config file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures in addition to errors",
    )
    args = parser.parse_args(argv)

    try:
        config = load_yaml(args.config)
    except FileNotFoundError:
        print(f"ERROR: {args.config}: file does not exist", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"ERROR: {args.config}: invalid YAML: {exc}", file=sys.stderr)
        return 2

    findings = lint_config(config)
    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARN"]

    for finding in findings:
        print(finding.render())

    if errors or (args.strict and warnings):
        print(
            f"Serve config lint failed: {len(errors)} error(s), {len(warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"Serve config lint passed: {len(warnings)} warning(s), "
        f"{len([f for f in findings if f.level == 'INFO'])} info note(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

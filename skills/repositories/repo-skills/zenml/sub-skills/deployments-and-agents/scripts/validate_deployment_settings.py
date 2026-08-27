#!/usr/bin/env python3
"""Validate ZenML deployment settings without starting services.

This helper is intentionally safe by default. It imports ZenML settings classes
when available and instantiates small payloads, but it never deploys pipelines,
starts servers, builds images, calls LLM providers, reads credentials, or
requires Docker.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXAMPLE_PAYLOAD: dict[str, Any] = {
    "deployment": {
        "app_title": "Credential-Free Deployment Smoke",
        "app_description": "Tiny validation payload for ZenML deployments.",
        "app_version": "0.1.0",
        "dashboard_files_path": "ui",
        "cors": {
            "allow_origins": ["*"],
            "allow_methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["*"],
            "allow_credentials": False,
        },
        "uvicorn_host": "0.0.0.0",
        "uvicorn_port": 8000,
    },
    "docker": {
        "requirements": "requirements.txt",
        "environment": {"OPENAI_API_KEY": "${OPENAI_API_KEY}"},
    },
}


@dataclass(frozen=True)
class ValidationResult:
    """Collected validation result details."""

    ok: bool
    messages: list[str]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Top-level JSON payload must be an object.")

    return payload


def import_settings_classes() -> tuple[type[Any], type[Any], type[Any] | None]:
    """Import ZenML settings classes with a clear error on missing deps."""

    try:
        from zenml.config import DeploymentSettings, DockerSettings
    except ModuleNotFoundError as exc:
        missing_name = exc.name or "unknown"
        raise RuntimeError(
            "Could not import ZenML deployment settings. Install ZenML in the "
            "active Python environment, for example `pip install zenml`. If "
            f"the missing module is optional (`{missing_name}`), install the "
            "narrow ZenML extra or integration needed for that environment."
        ) from exc
    except ImportError as exc:
        raise RuntimeError(
            "ZenML is importable, but deployment settings could not be loaded. "
            "This can indicate an incompatible ZenML install or missing "
            f"optional server/runtime dependency: {exc}"
        ) from exc

    try:
        from zenml.config import CORSConfig
    except ImportError:
        CORSConfig = None

    return DeploymentSettings, DockerSettings, CORSConfig


def model_to_dict(model: Any) -> dict[str, Any]:
    """Convert Pydantic v2 or v1 models to dictionaries."""

    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept either grouped or direct DeploymentSettings payloads."""

    if "deployment" in payload or "docker" in payload:
        return payload
    return {"deployment": payload}


def validate_payload(payload: dict[str, Any]) -> ValidationResult:
    """Instantiate settings classes for the supplied payload."""

    DeploymentSettings, DockerSettings, _ = import_settings_classes()
    grouped_payload = normalize_payload(payload)
    messages: list[str] = []

    deployment_payload = grouped_payload.get("deployment")
    docker_payload = grouped_payload.get("docker")

    if deployment_payload is None and docker_payload is None:
        raise ValueError(
            "Payload must contain `deployment`, `docker`, or direct "
            "DeploymentSettings fields."
        )

    if deployment_payload is not None:
        if not isinstance(deployment_payload, dict):
            raise ValueError("`deployment` must be a JSON object.")
        deployment_settings = DeploymentSettings(**deployment_payload)
        deployment_data = model_to_dict(deployment_settings)
        messages.append("DeploymentSettings: valid")
        messages.append(
            "Deployment endpoints: "
            f"invoke={deployment_data.get('invoke_url_path')}, "
            f"health={deployment_data.get('health_url_path')}, "
            f"docs={deployment_data.get('docs_url_path')}"
        )
        dashboard_path = deployment_data.get("dashboard_files_path")
        if dashboard_path:
            messages.append(
                "Dashboard files path is configured; ensure it is source-root "
                "relative and contains index.html before deploying."
            )

    if docker_payload is not None:
        if not isinstance(docker_payload, dict):
            raise ValueError("`docker` must be a JSON object.")
        docker_settings = DockerSettings(**docker_payload)
        docker_data = model_to_dict(docker_settings)
        messages.append("DockerSettings: valid")
        requirements = docker_data.get("requirements")
        if requirements:
            messages.append(f"Docker requirements configured: {requirements}")
        environment = docker_data.get("environment") or {}
        if environment:
            names = ", ".join(sorted(environment.keys()))
            messages.append(
                "Docker environment variable names configured "
                f"(values not inspected): {names}"
            )

    return ValidationResult(ok=True, messages=messages)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Safely validate ZenML DeploymentSettings and DockerSettings "
            "payloads without deploying or starting services."
        )
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Print and validate a tiny credential-free settings payload.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help=(
            "Path to a JSON object containing `deployment` and/or `docker` "
            "settings. A direct DeploymentSettings object is also accepted."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the settings validator."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.example and args.json is None:
        parser.print_help()
        return 0

    try:
        payload = EXAMPLE_PAYLOAD if args.example else load_json(args.json)
        if args.example:
            print(json.dumps(EXAMPLE_PAYLOAD, indent=2, sort_keys=True))
        result = validate_payload(payload)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for message in result.messages:
        print(message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

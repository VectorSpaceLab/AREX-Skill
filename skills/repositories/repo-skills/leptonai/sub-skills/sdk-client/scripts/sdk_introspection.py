#!/usr/bin/env python3
"""Print LeptonAI SDK import, signature, and API resource surfaces.

This script performs no network calls: it imports modules and inspects classes,
but it does not instantiate Client or APIClient and does not read credentials.
"""

from __future__ import annotations

import importlib
import inspect
from importlib import metadata
from typing import Iterable, List, Optional, Tuple, Type


RESOURCE_SURFACES = [
    ("nodegroup", "leptonai.api.v2.dedicated_node_groups", "DedicatedNodeGroupAPI"),
    ("job", "leptonai.api.v2.job", "JobAPI"),
    ("secret", "leptonai.api.v2.secret", "SecretAPI"),
    ("ingress", "leptonai.api.v2.ingress", "IngressAPI"),
    ("storage", "leptonai.api.v2.storage", "StorageAPI"),
    ("log", "leptonai.api.v2.log", "LogAPI"),
    ("template", "leptonai.api.v2.template", "TemplateAPI"),
    ("finetune", "leptonai.api.v2.finetune", "FineTuneAPI"),
    ("shapes", "leptonai.api.v2.resource_shape", "ResourceShapeAPI"),
    ("raycluster", "leptonai.api.v2.raycluster", "RayClusterAPI"),
]

DYNAMIC_SURFACES = [
    ("deployment (legacy)", "leptonai.api.v2.deployment", "DeploymentAPI"),
    ("deployment (new endpoint mode)", "leptonai.api.v2.endpoint", "EndpointAPI"),
    ("pod (legacy)", "leptonai.api.v2.pod", "PodAPI"),
    ("pod (new devpod mode)", "leptonai.api.v2.devpod", "DevPodAPI"),
]


def public_methods(cls: Type[object]) -> List[str]:
    """Return public methods declared on a class, preserving definition order."""
    methods: List[str] = []
    for name, value in cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(value, (staticmethod, classmethod)):
            value = value.__func__
        if inspect.isfunction(value):
            methods.append(name)
    return methods


def import_class(module_name: str, class_name: str) -> Type[object]:
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def print_signature(label: str, obj: object) -> None:
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError) as exc:
        print(f"{label}: <signature unavailable: {exc}>")
    else:
        print(f"{label}: {signature}")


def dump_model(model: object) -> dict:
    """Serialize a Pydantic model across v1/v2 for display only."""
    if hasattr(model, "model_dump"):
        return model.model_dump(by_alias=True, exclude_none=True)  # type: ignore[attr-defined]
    return model.dict(by_alias=True, exclude_none=True)  # type: ignore[attr-defined]


def print_methods(rows: Iterable[Tuple[str, str, str]]) -> None:
    for attr_name, module_name, class_name in rows:
        cls = import_class(module_name, class_name)
        methods = public_methods(cls)
        method_text = ", ".join(methods) if methods else "<no public methods>"
        print(f"- {attr_name}: {module_name}.{class_name}")
        print(f"  methods: {method_text}")


def main() -> int:
    try:
        dist_version = metadata.version("leptonai")
    except metadata.PackageNotFoundError:
        dist_version = "<distribution metadata not found>"

    import leptonai
    from leptonai.client import Client, PathTree, current, local
    from leptonai.api.v2.api_resource import APIResourse
    from leptonai.api.v2.client import APIClient, reset_new_deployment_api_flag_cache
    from leptonai.api.v2.spec_utils import (
        make_env_vars_from_strings,
        make_mounts_from_strings,
    )
    from leptonai.config import PYDANTIC_MAJOR_VERSION

    print("LeptonAI SDK introspection (no network calls)")
    print("=" * 52)
    print(f"distribution version: {dist_version}")
    print(f"module __version__: {getattr(leptonai, '__version__', '<missing>')}")
    print(f"pydantic major version detected by leptonai: {PYDANTIC_MAJOR_VERSION}")
    print()

    print("Signatures")
    print("-" * 52)
    print_signature("Client", Client)
    print_signature("local", local)
    print_signature("current", current)
    print_signature("APIClient", APIClient)
    print_signature("reset_new_deployment_api_flag_cache", reset_new_deployment_api_flag_cache)
    print_signature("APIResourse.safe_json", APIResourse.safe_json)
    print_signature("make_mounts_from_strings", make_mounts_from_strings)
    print_signature("make_env_vars_from_strings", make_env_vars_from_strings)
    print()

    print("PathTree naming examples")
    print("-" * 52)
    for raw in ["run", "foo-bar", "foo.bar", "class", "{item_id}"]:
        print(f"{raw!r} -> {PathTree.rectify_name(raw)!r}; valid={PathTree.rectify_name(raw).isidentifier()}")
    print(f"local(8080) -> {local(8080)}")
    print()

    print("APIClient resource attributes")
    print("-" * 52)
    print_methods(RESOURCE_SURFACES)
    print()

    print("Dynamic deployment/pod dispatch surfaces")
    print("-" * 52)
    print("Accessing APIClient.deployment or APIClient.pod may resolve a workspace feature flag; the classes below are inspected without property access.")
    print_methods(DYNAMIC_SURFACES)
    print()

    print("Spec helper smoke")
    print("-" * 52)
    resource = APIResourse.__new__(APIResourse)
    mounts = make_mounts_from_strings(["/data:/mnt/data:node-local"])
    envs = make_env_vars_from_strings(["MODE=test"], ["API_SECRET"])
    print("mounts:", [dump_model(item) for item in mounts or []])
    print("envs:", [dump_model(item) for item in envs or []])
    print("safe_json mount:", resource.safe_json((mounts or [])[0]) if mounts else None)
    print()
    print("Done. No Client or APIClient instance was constructed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

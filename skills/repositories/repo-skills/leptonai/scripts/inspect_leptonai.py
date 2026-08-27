#!/usr/bin/env python3
"""Inspect installed LeptonAI APIs without live workspace calls.

This helper imports modules, prints versions/signatures, and optionally walks the
installed Click command tree in memory. It does not instantiate `Client` or
`APIClient` and does not contact a Lepton workspace.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from importlib import metadata
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

RESOURCE_CLASSES = [
    ("deployment", "leptonai.api.v2.deployment", "DeploymentAPI"),
    ("endpoint", "leptonai.api.v2.endpoint", "EndpointAPI"),
    ("pod", "leptonai.api.v2.pod", "PodAPI"),
    ("devpod", "leptonai.api.v2.devpod", "DevPodAPI"),
    ("job", "leptonai.api.v2.job", "JobAPI"),
    ("storage", "leptonai.api.v2.storage", "StorageAPI"),
    ("secret", "leptonai.api.v2.secret", "SecretAPI"),
    ("ingress", "leptonai.api.v2.ingress", "IngressAPI"),
    ("raycluster", "leptonai.api.v2.raycluster", "RayClusterAPI"),
    ("finetune", "leptonai.api.v2.finetune", "FineTuneAPI"),
    ("template", "leptonai.api.v2.template", "TemplateAPI"),
    ("resource_shape", "leptonai.api.v2.resource_shape", "ResourceShapeAPI"),
    ("log", "leptonai.api.v2.log", "LogAPI"),
]


def import_obj(module_name: str, object_name: str) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<unavailable: {exc}>"


def public_methods(cls: Type[object]) -> List[str]:
    methods: List[str] = []
    for name, value in cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(value, (staticmethod, classmethod)):
            value = value.__func__
        if inspect.isfunction(value):
            methods.append(name)
    return methods


def collect_api() -> dict:
    import leptonai
    from leptonai.client import Client, PathTree, current, local
    from leptonai.api.v2.api_resource import APIResourse
    from leptonai.api.v2.client import APIClient, reset_new_deployment_api_flag_cache
    from leptonai.api.v2.spec_utils import make_env_vars_from_strings, make_mounts_from_strings
    from leptonai.config import PYDANTIC_MAJOR_VERSION

    classes = []
    for label, module_name, class_name in RESOURCE_CLASSES:
        cls = import_obj(module_name, class_name)
        classes.append({"label": label, "class": f"{module_name}.{class_name}", "methods": public_methods(cls)})

    return {
        "distribution_version": metadata.version("leptonai"),
        "module_version": getattr(leptonai, "__version__", None),
        "pydantic_major_version": PYDANTIC_MAJOR_VERSION,
        "signatures": {
            "Client": signature_text(Client),
            "local": signature_text(local),
            "current": signature_text(current),
            "APIClient": signature_text(APIClient),
            "APIResourse.safe_json": signature_text(APIResourse.safe_json),
            "reset_new_deployment_api_flag_cache": signature_text(reset_new_deployment_api_flag_cache),
            "make_mounts_from_strings": signature_text(make_mounts_from_strings),
            "make_env_vars_from_strings": signature_text(make_env_vars_from_strings),
        },
        "path_tree_rectify_examples": {raw: PathTree.rectify_name(raw) for raw in ["run", "foo-bar", "foo.bar", "class", "{item_id}"]},
        "local_8080": local(8080),
        "resource_classes": classes,
    }


def collect_cli_tree() -> List[Dict[str, Any]]:
    from click.core import Group
    from leptonai.cli import lep

    rows: List[Dict[str, Any]] = []

    def walk(command: Any, path: Tuple[str, ...]) -> None:
        if not isinstance(command, Group):
            return
        for name, sub in command.commands.items():
            sub_path = path + (name,)
            rows.append({
                "command": " ".join(sub_path),
                "hidden": bool(getattr(sub, "hidden", False)),
                "short_help": (getattr(sub, "short_help", None) or "").replace("\n", " "),
            })
            walk(sub, sub_path)

    walk(lep, ("lep",))
    return rows


def print_text(data: dict) -> None:
    print("LeptonAI installed API inspection (no live workspace calls)")
    print(f"version: {data['api']['distribution_version']}")
    print("signatures:")
    for name, sig in data["api"]["signatures"].items():
        print(f"  - {name}{sig}")
    print("resource classes:")
    for item in data["api"]["resource_classes"]:
        print(f"  - {item['label']}: {item['class']} -> {', '.join(item['methods']) or '<none>'}")
    if data.get("cli_tree"):
        print("cli commands:")
        for row in data["cli_tree"]:
            hidden = " hidden" if row["hidden"] else ""
            print(f"  - {row['command']}{hidden}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect LeptonAI installed API and optional Click command tree without live calls.")
    parser.add_argument("--include-cli-tree", action="store_true", help="Also import leptonai.cli and print registered Click command tree in memory.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    data = {"api": collect_api()}
    if args.include_cli_tree:
        data["cli_tree"] = collect_cli_tree()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

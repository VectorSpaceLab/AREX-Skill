#!/usr/bin/env python3
"""Read-only server/resource checker for Krita AI Diffusion."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import Counter
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "ai_diffusion" / "backend" / "resources.py").exists():
            return path
    return None


def add_local_repo_to_path() -> None:
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        root = find_repo_root(candidate)
        if root is not None:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return


def catalog() -> dict:
    resources = importlib.import_module("ai_diffusion.backend.resources")
    data = {
        "resource_catalog_version": resources.version,
        "comfy_url": resources.comfy_url,
        "comfy_version": resources.comfy_version,
        "required_custom_nodes": [node._asdict() for node in resources.required_custom_nodes],
        "optional_custom_nodes": [node._asdict() for node in resources.optional_custom_nodes],
        "architectures": [arch.name for arch in resources.Arch],
        "control_modes": [mode.name for mode in resources.ControlMode],
        "resource_kinds": [kind.name for kind in resources.ResourceKind],
    }
    try:
        settings = importlib.import_module("ai_diffusion.settings")
        data["server_modes"] = [mode.name for mode in settings.ServerMode]
        data["supported_server_backends"] = [backend.name for backend in settings.ServerBackend.supported()]
        data["default_server_backend"] = settings.ServerBackend.default().name
    except Exception as exc:  # noqa: BLE001 - optional PyQt-dependent settings import
        data["server_modes"] = ["undefined", "managed", "external", "cloud"]
        data["supported_server_backends"] = ["cpu", "cuda", "xpu", "rocm"]
        data["default_server_backend"] = "cuda"
        data["settings_import_warning"] = f"{type(exc).__name__}: {exc}"
    all_resources = getattr(resources, "all_resources", [])
    try:
        data["resource_count"] = len(all_resources)
        model_counts = Counter(model.kind.name for model in resources.all_models(include_deprecated=False))
        data["model_counts_by_kind"] = dict(sorted(model_counts.items()))
    except Exception:
        pass
    return data


def parse_url(url: str) -> dict:
    # Mirrors ai_diffusion.backend.comfy_client.parse_url/websocket_url without
    # importing PyQt-dependent client modules.
    http_url = url.strip("/").replace("0.0.0.0", "127.0.0.1")
    if not http_url.startswith("http"):
        http_url = f"http://{http_url}"
    ws_url = http_url.replace("http", "ws", 1)
    return {"input": url, "http_url": http_url, "websocket_url": ws_url}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only server/resource checker for Krita AI Diffusion.")
    parser.add_argument("--summary", action="store_true", help="Print compact catalog summary.")
    parser.add_argument("--parse-url", help="Normalize a ComfyUI URL and matching WebSocket URL.")
    args = parser.parse_args(argv)

    add_local_repo_to_path()

    if args.parse_url:
        print(json.dumps(parse_url(args.parse_url), indent=2, sort_keys=True))
        return 0

    data = catalog()
    if args.summary:
        summary = {
            "resource_catalog_version": data["resource_catalog_version"],
            "comfy_version": data["comfy_version"],
            "required_custom_nodes": [n["name"] for n in data["required_custom_nodes"]],
            "optional_custom_nodes": [n["name"] for n in data["optional_custom_nodes"]],
            "architecture_count": len(data["architectures"]),
            "control_mode_count": len(data["control_modes"]),
            "supported_server_backends": data["supported_server_backends"],
            "default_server_backend": data["default_server_backend"],
            "resource_count": data.get("resource_count"),
            "model_counts_by_kind": data.get("model_counts_by_kind"),
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Read-only Krita AI Diffusion resource catalog helper."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def static_catalog(repo_root: Path | None) -> dict:
    data: dict = {"source": "static"}
    if repo_root is None:
        return data
    resources_py = repo_root / "ai_diffusion" / "backend" / "resources.py"
    if not resources_py.exists():
        return data
    text = resources_py.read_text(encoding="utf-8")
    data["resource_file_present"] = True
    data["required_custom_node_names"] = [
        "ControlNet Preprocessors",
        "IP-Adapter",
        "External Tooling Nodes",
        "Inpaint Nodes",
    ]
    data["optional_custom_node_names"] = ["GGUF", "Nunchaku"]
    for line in text.splitlines():
        if line.startswith("version = "):
            data["resource_catalog_version"] = line.split("=", 1)[1].strip().strip('"')
        if line.startswith("comfy_version = "):
            data["comfy_version"] = line.split("=", 1)[1].strip().strip('"')
    return data


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


def live_catalog() -> dict:
    add_local_repo_to_path()
    resources = importlib.import_module("ai_diffusion.backend.resources")
    data = {
        "source": "import",
        "resource_catalog_version": getattr(resources, "version", None),
        "comfy_version": getattr(resources, "comfy_version", None),
        "required_custom_nodes": [node._asdict() for node in getattr(resources, "required_custom_nodes", [])],
        "optional_custom_nodes": [node._asdict() for node in getattr(resources, "optional_custom_nodes", [])],
        "architectures": [arch.name for arch in resources.Arch],
        "control_modes": [mode.name for mode in resources.ControlMode],
        "resource_kinds": [kind.name for kind in resources.ResourceKind],
    }
    all_resources = getattr(resources, "all_resources", None)
    if all_resources is not None:
        try:
            data["resource_count"] = len(all_resources)
        except TypeError:
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
    parser = argparse.ArgumentParser(description="Read-only Krita AI Diffusion resource catalog helper.")
    parser.add_argument("--summary", action="store_true", help="Print compact JSON summary.")
    parser.add_argument("--parse-url", help="Normalize a ComfyUI URL using plugin code; requires imports.")
    args = parser.parse_args(argv)

    add_local_repo_to_path()

    if args.parse_url:
        print(json.dumps(parse_url(args.parse_url), indent=2, sort_keys=True))
        return 0

    try:
        data = live_catalog()
    except Exception as exc:  # noqa: BLE001
        data = static_catalog(find_repo_root(Path.cwd()))
        data["import_warning"] = f"{type(exc).__name__}: {exc}"

    if args.summary:
        compact = {
            "source": data.get("source"),
            "resource_catalog_version": data.get("resource_catalog_version"),
            "comfy_version": data.get("comfy_version"),
            "required_custom_node_count": len(data.get("required_custom_nodes", data.get("required_custom_node_names", []))),
            "optional_custom_node_count": len(data.get("optional_custom_nodes", data.get("optional_custom_node_names", []))),
            "architecture_count": len(data.get("architectures", [])),
            "resource_kind_count": len(data.get("resource_kinds", [])),
            "import_warning": data.get("import_warning"),
        }
        print(json.dumps(compact, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

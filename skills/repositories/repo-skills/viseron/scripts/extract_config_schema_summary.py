#!/usr/bin/env python3
"""Summarize Viseron component schema/setup availability without writing docs."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass
from typing import Any

COMPONENTS = [
    "background_subtractor",
    "codeprojectai",
    "compreface",
    "darknet",
    "deepstack",
    "discord",
    "dlib",
    "edgetpu",
    "ffmpeg",
    "go2rtc",
    "gotify",
    "gstreamer",
    "hailo",
    "logger",
    "mog2",
    "mqtt",
    "nvr",
    "ptz",
    "storage",
    "telegram",
    "webhook",
    "webserver",
    "yolo",
]


@dataclass
class ComponentSummary:
    component: str
    import_ok: bool
    has_config_schema: bool = False
    has_setup: bool = False
    has_setup_domains: bool = False
    config_top_key: str | None = None
    description: str | None = None
    error_type: str | None = None
    error: str | None = None


def summarize(component: str) -> ComponentSummary:
    try:
        module = importlib.import_module(f"viseron.components.{component}")
    except Exception as exc:  # noqa: BLE001 - diagnostic helper reports optional import failures.
        return ComponentSummary(
            component=component,
            import_ok=False,
            error_type=type(exc).__name__,
            error=str(exc),
        )

    top_key: str | None = None
    description: str | None = None
    try:
        const = importlib.import_module(f"viseron.components.{component}.const")
        top_key = getattr(const, "COMPONENT", component)
        description = getattr(const, "DESC_COMPONENT", None)
    except Exception:  # noqa: BLE001 - constants are optional for this summary.
        top_key = component

    return ComponentSummary(
        component=component,
        import_ok=True,
        has_config_schema=hasattr(module, "CONFIG_SCHEMA"),
        has_setup=hasattr(module, "setup"),
        has_setup_domains=hasattr(module, "setup_domains"),
        config_top_key=top_key,
        description=description,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "components",
        nargs="*",
        help="Component names to inspect. Defaults to all known Viseron components.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    names = args.components or COMPONENTS
    results = [summarize(name) for name in names]

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            if result.import_ok:
                hooks = []
                if result.has_config_schema:
                    hooks.append("CONFIG_SCHEMA")
                if result.has_setup:
                    hooks.append("setup")
                if result.has_setup_domains:
                    hooks.append("setup_domains")
                print(f"{result.component}: top_key={result.config_top_key} hooks={','.join(hooks) or 'none'}")
                if result.description:
                    print(f"  description: {result.description}")
            else:
                print(f"{result.component}: IMPORT_FAIL {result.error_type}: {result.error}")

    return 0 if all(result.import_ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

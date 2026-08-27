#!/usr/bin/env python3
"""Probe Viseron core and optional imports without contacting cameras or services."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable

CORE_MODULES = [
    "viseron",
    "viseron.config",
    "viseron.reload",
    "viseron.components",
    "viseron.domains",
    "viseron.helpers.validators",
    "viseron.events",
    "viseron.states",
]

OPTIONAL_MODULES = {
    "ffmpeg": ["viseron.components.ffmpeg", "viseron.components.ffmpeg.stream"],
    "gstreamer": ["viseron.components.gstreamer", "viseron.components.gstreamer.camera"],
    "storage": ["viseron.components.storage", "viseron.components.storage.models"],
    "webserver": ["viseron.components.webserver"],
    "mqtt": ["viseron.components.mqtt"],
    "telegram": ["viseron.components.telegram"],
    "ptz": ["viseron.components.ptz"],
    "codeprojectai": ["viseron.components.codeprojectai"],
    "deepstack": ["viseron.components.deepstack"],
    "compreface": ["viseron.components.compreface"],
    "dlib": ["viseron.components.dlib"],
    "darknet": ["viseron.components.darknet"],
    "edgetpu": ["viseron.components.edgetpu"],
    "hailo": ["viseron.components.hailo"],
    "yolo": ["viseron.components.yolo"],
}


@dataclass
class ProbeResult:
    name: str
    ok: bool
    error_type: str | None = None
    error: str | None = None
    hint: str | None = None


def hint_for(error: BaseException) -> str | None:
    text = str(error)
    if "No module named 'manager'" in text or 'No module named "manager"' in text:
        return "Run source-development commands from the Viseron source root or put that source root on PYTHONPATH so manager.py is visible."
    if "No module named 'gi'" in text or 'No module named "gi"' in text:
        return "Install PyGObject/GStreamer system bindings, or use the FFmpeg component instead."
    if "hailo_platform" in text:
        return "Install the target host Hailo runtime and expose the Hailo device to the Viseron runtime."
    if "telegram" in text:
        return "Install python-telegram-bot when Telegram notifications/control are selected."
    if "onvif" in text or "zeep" in text:
        return "Install ONVIF client dependencies when PTZ control is selected."
    return None


def probe_module(module: str) -> ProbeResult:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic probe should report all import failures.
        return ProbeResult(
            name=module,
            ok=False,
            error_type=type(exc).__name__,
            error=str(exc),
            hint=hint_for(exc),
        )
    return ProbeResult(name=module, ok=True)


def selected_optional(names: Iterable[str]) -> list[str]:
    selected: list[str] = []
    for name in names:
        if name == "all":
            return sorted(OPTIONAL_MODULES)
        if name not in OPTIONAL_MODULES:
            raise SystemExit(f"Unknown optional group {name!r}; choose from {', '.join(sorted(OPTIONAL_MODULES))} or all")
        selected.append(name)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--optional",
        action="append",
        default=[],
        help="Optional component group to probe; repeat or use 'all'.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    results: list[ProbeResult] = []
    for module in CORE_MODULES:
        results.append(probe_module(module))
    for group in selected_optional(args.optional):
        for module in OPTIONAL_MODULES[group]:
            results.append(probe_module(module))

    version: str | None
    try:
        version = metadata.version("viseron")
    except metadata.PackageNotFoundError:
        version = None

    payload = {
        "distribution": "viseron",
        "version": version,
        "results": [asdict(result) for result in results],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"viseron distribution version: {version or 'not-installed'}")
        for result in results:
            if result.ok:
                print(f"OK   {result.name}")
            else:
                print(f"FAIL {result.name}: {result.error_type}: {result.error}")
                if result.hint:
                    print(f"     hint: {result.hint}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

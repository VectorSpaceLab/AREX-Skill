#!/usr/bin/env python3
"""Inspect Dash backend, async, background, and optional-extra availability.

This helper imports Dash backends and reports which optional extras are present
without starting a server. It is safe to run from any working directory.

Examples:
    python inspect_backends.py
    python inspect_backends.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Item:
    name: str
    ok: bool
    detail: str


def try_import(name: str, hint: str | None = None) -> Item:
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        detail = f"imported{f' version={version}' if version else ''}"
        return Item(name, True, detail)
    except Exception as exc:  # pragma: no cover - diagnostic path
        detail = f"{type(exc).__name__}: {exc}"
        if hint:
            detail += f"; install {hint}"
        return Item(name, False, detail)


def try_backend(name: str) -> Item:
    try:
        from dash.backends import get_backend
        from dash import Dash

        cls = get_backend(name)
        app = Dash(__name__) if name == "flask" else Dash(__name__, backend=name)
        return Item(f"backend:{name}", True, f"{cls.__name__}, app.backend={app.backend.server_type}")
    except Exception as exc:  # pragma: no cover - depends on optional extras
        hints = {
            "flask": "dash",
            "fastapi": "dash[fastapi]",
            "quart": "dash[quart]",
        }
        return Item(f"backend:{name}", False, f"{type(exc).__name__}: {exc}; install {hints[name]} if required")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect Dash backend and optional-extra availability.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    checks: list[Item] = []
    for module, hint in [
        ("dash", None),
        ("diskcache", "dash[diskcache]"),
        ("celery", "dash[celery] plus broker/result backend"),
        ("asgiref", "dash[async] for Flask async callbacks"),
        ("fastapi", "dash[fastapi]"),
        ("quart", "dash[quart]"),
        ("selenium", "dash[testing] plus a browser/driver"),
    ]:
        checks.append(try_import(module, hint))

    for backend in ["flask", "fastapi", "quart"]:
        checks.append(try_backend(backend))

    payload: dict[str, Any] = {
        "ok": all(item.ok for item in checks if item.name in {"dash", "backend:flask", "backend:fastapi", "backend:quart"}),
        "checks": [asdict(item) for item in checks],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in checks:
            status = "OK" if item.ok else "WARN"
            print(f"[{status}] {item.name}: {item.detail}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

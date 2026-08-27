#!/usr/bin/env python3
"""Safe Dash installation diagnostic.

This helper imports Dash, checks key public symbols, probes optional backend
packages without starting a server, and checks Dash CLI entry points by running
`--help`. It does not need a Dash source checkout and does not open a browser.

Examples:
    python check_dash_install.py
    python check_dash_install.py --json
    python check_dash_install.py --skip-cli
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def try_import(name: str) -> Check:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        suffix = f" version={version}" if version else ""
        return Check(name, True, f"imported{suffix}")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return Check(name, False, f"{type(exc).__name__}: {exc}")


def check_dash_symbols() -> list[Check]:
    checks: list[Check] = []
    try:
        import dash
        from dash import Dash, html, dcc, Input, Output, State, callback, clientside_callback, Patch

        checks.append(Check("dash", True, f"version={dash.__version__}"))
        for label, obj in [
            ("Dash", Dash),
            ("html.Div", getattr(html, "Div", None)),
            ("dcc.Graph", getattr(dcc, "Graph", None)),
            ("Input", Input),
            ("Output", Output),
            ("State", State),
            ("callback", callback),
            ("clientside_callback", clientside_callback),
            ("Patch", Patch),
        ]:
            checks.append(Check(label, obj is not None, repr(obj) if obj is not None else "missing"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks.append(Check("dash public symbols", False, f"{type(exc).__name__}: {exc}"))
    return checks


def check_backend_creation() -> list[Check]:
    checks: list[Check] = []
    try:
        from dash import Dash
        from dash.backends import get_backend
    except Exception as exc:  # pragma: no cover
        return [Check("dash.backends", False, f"{type(exc).__name__}: {exc}")]

    for backend in ["flask", "fastapi", "quart"]:
        try:
            cls = get_backend(backend)
            app = Dash(__name__, backend=backend) if backend != "flask" else Dash(__name__)
            checks.append(Check(f"backend:{backend}", True, f"{cls.__name__}, app.backend={app.backend.server_type}"))
        except Exception as exc:  # pragma: no cover - depends on extras
            extra = {"fastapi": "dash[fastapi]", "quart": "dash[quart]", "flask": "dash"}[backend]
            checks.append(Check(f"backend:{backend}", False, f"{type(exc).__name__}: {exc}; install {extra} if this backend is required"))
    return checks


def check_optional_modules() -> list[Check]:
    modules = [
        ("diskcache", "dash[diskcache]"),
        ("celery", "dash[celery] plus broker/result backend"),
        ("asgiref", "dash[async] for Flask async callbacks"),
        ("selenium", "dash[testing] plus browser/driver"),
        ("fastapi", "dash[fastapi]"),
        ("quart", "dash[quart]"),
    ]
    checks: list[Check] = []
    for module, hint in modules:
        result = try_import(module)
        if not result.ok:
            result.detail += f"; install {hint} if required"
        checks.append(result)
    return checks


def check_cli(command: str) -> Check:
    exe = shutil.which(command)
    if not exe:
        return Check(f"cli:{command}", False, "not on PATH")
    try:
        proc = subprocess.run([exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
    except Exception as exc:  # pragma: no cover
        return Check(f"cli:{command}", False, f"{type(exc).__name__}: {exc}")
    output = (proc.stdout or proc.stderr).strip().splitlines()
    first = output[0] if output else "no help output"
    return Check(f"cli:{command}", proc.returncode == 0, f"exit={proc.returncode}; {first}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Dash imports, optional backends, and safe CLI help.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip CLI --help checks.")
    args = parser.parse_args(argv)

    checks = []
    checks.extend(check_dash_symbols())
    checks.extend(check_backend_creation())
    checks.extend(check_optional_modules())
    if not args.skip_cli:
        for command in ["dash-generate-components", "dash-update-components", "renderer"]:
            checks.append(check_cli(command))

    payload: dict[str, Any] = {
        "python": sys.executable,
        "ok": all(c.ok for c in checks if not c.name.startswith(("celery", "selenium", "backend:fastapi", "backend:quart"))),
        "checks": [asdict(c) for c in checks],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for c in checks:
            status = "OK" if c.ok else "WARN"
            print(f"[{status}] {c.name}: {c.detail}")
    required_failed = [c for c in checks if not c.ok and c.name in {"dash public symbols", "dash", "Dash", "html.Div", "dcc.Graph", "Input", "Output", "State"}]
    return 1 if required_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

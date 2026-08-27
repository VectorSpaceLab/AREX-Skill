#!/usr/bin/env python3
"""Read-only Triton environment/package checker.

The checker imports common Triton packages, probes optional commands, and can
query a live HTTP readiness endpoint when explicitly given --url. It never
starts Triton, pulls images, downloads models, or mutates the environment.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Result:
    name: str
    status: str
    detail: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    ok: bool
    results: list[Result]
    notes: list[str]


def check_distribution(dist_name: str, import_name: str | None = None) -> Result:
    import_name = import_name or dist_name.replace('-', '_')
    try:
        version = md.version(dist_name)
    except md.PackageNotFoundError:
        return Result(dist_name, "missing", f"distribution {dist_name!r} is not installed")
    try:
        mod = importlib.import_module(import_name)
    except Exception as exc:  # native imports can fail with ABI/library errors
        return Result(dist_name, "import-failed", f"{type(exc).__name__}: {exc}", {"version": version, "import_name": import_name})
    return Result(dist_name, "ok", f"import {import_name!r} succeeded", {"version": version, "module": getattr(mod, "__name__", import_name)})


def check_command(command: str) -> Result:
    path = shutil.which(command)
    if not path:
        return Result(command, "missing", f"{command!r} not found on PATH")
    try:
        proc = subprocess.run([command, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8, check=False)
        first = (proc.stdout or "").splitlines()[0] if proc.stdout else f"exit {proc.returncode}"
        return Result(command, "ok" if proc.returncode == 0 else "warning", first, {"path": path, "returncode": proc.returncode})
    except Exception as exc:
        return Result(command, "warning", f"could not run --version: {type(exc).__name__}: {exc}", {"path": path})


def check_url(url: str, timeout: float) -> Result:
    target = url.rstrip('/') + '/v2/health/ready'
    try:
        req = urllib.request.Request(target, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return Result('triton-http-ready', 'ok', f"{target} returned HTTP {response.status}", {"url": target})
    except urllib.error.HTTPError as exc:
        return Result('triton-http-ready', 'not-ready', f"{target} returned HTTP {exc.code}", {"url": target})
    except Exception as exc:
        return Result('triton-http-ready', 'unreachable', f"{type(exc).__name__}: {exc}", {"url": target})


def build_report(args: argparse.Namespace) -> Report:
    results = [
        check_distribution('tritonclient', 'tritonclient'),
        check_distribution('tritonserver', 'tritonserver'),
        check_distribution('tritonfrontend', 'tritonfrontend'),
        check_distribution('openai', 'openai'),
    ]
    if not args.skip_commands:
        for command in ('tritonserver', 'docker'):
            results.append(check_command(command))
    if args.url:
        results.append(check_url(args.url, args.timeout))
    notes = [
        'This checker is read-only; it does not start Triton, Docker, downloads, or model loads.',
        'A package import check is not proof that a live Triton model can load or infer.'
    ]
    has_hard_failure = any(r.status in {'import-failed', 'error'} for r in results)
    has_positive_signal = any(r.status == 'ok' for r in results)
    ok = (not has_hard_failure) and has_positive_signal
    if not has_positive_signal:
        notes.append('No positive Triton package, command, or URL signal was found; install a Triton client/server package or point the checker at a live endpoint.')
    return Report(ok=ok, results=results, notes=notes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print JSON instead of text.')
    parser.add_argument('--url', help='Base URL of a live Triton HTTP endpoint to probe, for example http://localhost:8000.')
    parser.add_argument('--timeout', type=float, default=3.0, help='URL probe timeout in seconds.')
    parser.add_argument('--skip-commands', action='store_true', help='Skip PATH command probes such as tritonserver and docker.')
    args = parser.parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print('Triton environment check:', 'OK' if report.ok else 'ATTENTION')
        for r in report.results:
            print(f"- {r.name}: {r.status} - {r.detail}")
        for note in report.notes:
            print(f"note: {note}")
    return 0 if report.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safely inspect pyQuil/QVM/quilc readiness without starting or invoking services.

Default mode performs only local checks: pyQuil importability, executable lookup,
configuration-path presence, and redacted URL environment metadata. It makes no
network requests and never reads or prints settings/secrets contents.

Examples:
  python check_services.py
  python check_services.py --probe-network --timeout 1
  python check_services.py --strict --qvm-url http://127.0.0.1:5000 \
      --quilc-url tcp://127.0.0.1:5555
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_QVM_URL = "http://127.0.0.1:5000"
DEFAULT_QUILC_URL = "tcp://127.0.0.1:5555"


def _redact_url(value: str) -> str:
    """Return scheme/host/port only; omit credentials, path, query, and fragment."""
    try:
        parsed = urlsplit(value)
        if not parsed.scheme or not parsed.hostname:
            return "<invalid-url>"
        try:
            port = parsed.port
        except ValueError:
            return f"{parsed.scheme}://<invalid-port>"
        suffix = f":{port}" if port is not None else ""
        return f"{parsed.scheme}://{parsed.hostname}{suffix}"
    except Exception:
        return "<unreadable-url>"


def _url_target(value: str) -> tuple[str, int] | None:
    """Extract a TCP target without performing a request."""
    parsed = urlsplit(value)
    if not parsed.hostname:
        return None
    if parsed.port is not None:
        return parsed.hostname, parsed.port
    if parsed.scheme in {"http", "https"}:
        return parsed.hostname, 443 if parsed.scheme == "https" else 80
    if parsed.scheme == "tcp":
        return parsed.hostname, 5555
    return None


def _probe(value: str, timeout: float) -> tuple[bool, str]:
    target = _url_target(value)
    if target is None:
        return False, "cannot derive host/port"
    try:
        with socket.create_connection(target, timeout=timeout):
            return True, f"TCP reachable at {target[0]}:{target[1]}"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _config_path(env_name: str, default: Path) -> Path:
    configured = os.environ.get(env_name)
    return Path(configured).expanduser() if configured else default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probe-network",
        action="store_true",
        help="opt in to bounded TCP reachability probes; default makes no network requests",
    )
    parser.add_argument("--timeout", type=float, default=1.0, help="per-probe timeout in seconds (default: 1.0)")
    parser.add_argument("--qvm-url", default=None, help="URL to probe instead of the configured/default QVM URL")
    parser.add_argument("--quilc-url", default=None, help="URL to probe instead of the configured/default quilc URL")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return nonzero when pyQuil is unavailable or an opted-in probe fails",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    print("pyQuil/QVM/quilc readiness (safe mode by default)")
    try:
        pyquil = importlib.import_module("pyquil")
    except Exception as exc:  # import diagnostics should remain concise
        print(f"pyquil import: FAIL ({type(exc).__name__}: {exc})")
        import_ok = False
    else:
        print(f"pyquil import: OK (version {getattr(pyquil, '__version__', 'unknown')})")
        import_ok = True

    for binary in ("qvm", "quilc"):
        found = shutil.which(binary)
        print(f"{binary} executable: {'FOUND' if found else 'MISSING'}")

    home = Path.home()
    settings = _config_path("QCS_SETTINGS_FILE_PATH", home / ".qcs" / "settings.toml")
    secrets = _config_path("QCS_SECRETS_FILE_PATH", home / ".qcs" / "secrets.toml")
    print(f"settings file: {'PRESENT' if settings.is_file() else 'ABSENT'} ({settings})")
    print(f"secrets file: {'PRESENT' if secrets.is_file() else 'ABSENT'} ({secrets}); contents not read")

    env_urls = {
        "QCS_SETTINGS_APPLICATIONS_QVM_URL": os.environ.get("QCS_SETTINGS_APPLICATIONS_QVM_URL"),
        "QCS_SETTINGS_APPLICATIONS_QUILC_URL": os.environ.get("QCS_SETTINGS_APPLICATIONS_QUILC_URL"),
    }
    for name, value in env_urls.items():
        if value is None:
            print(f"{name}: ABSENT")
        else:
            print(f"{name}: PRESENT ({_redact_url(value)})")

    probe_failed = False
    if args.probe_network:
        qvm_url = args.qvm_url or env_urls["QCS_SETTINGS_APPLICATIONS_QVM_URL"] or DEFAULT_QVM_URL
        quilc_url = args.quilc_url or env_urls["QCS_SETTINGS_APPLICATIONS_QUILC_URL"] or DEFAULT_QUILC_URL
        for label, url in (("qvm", qvm_url), ("quilc", quilc_url)):
            ok, detail = _probe(url, args.timeout)
            print(f"{label} endpoint {_redact_url(url)}: {'REACHABLE' if ok else 'UNREACHABLE'} ({detail})")
            probe_failed |= not ok
    else:
        print("network probes: SKIPPED (pass --probe-network to opt in)")

    if args.strict and (not import_ok or (args.probe_network and probe_failed)):
        return 2
    # Missing local binaries/config is useful information and is not an error in
    # a service-free/PyQVM environment unless the caller requested --strict.
    return 0


if __name__ == "__main__":
    sys.exit(main())

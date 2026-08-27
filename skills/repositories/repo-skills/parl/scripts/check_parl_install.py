#!/usr/bin/env python3
"""Safe PARL installation and backend diagnostic.

This root-level helper does not run training, start xparl services, download data,
or mutate files. Use sub-skill helpers for deeper workflow checks.

Examples:
  python scripts/check_parl_install.py
  python scripts/check_parl_install.py --backend torch --xparl-help --json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys


def item(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PARL import, backend aliases, and optional xparl help.")
    parser.add_argument("--backend", choices=["auto", "torch", "paddle", "fluid"], default="auto", help="Set PARL_BACKEND before importing parl; auto leaves the environment unchanged.")
    parser.add_argument("--xparl-help", action="store_true", help="Run xparl --help and xparl start --help without starting a cluster.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    if args.backend != "auto":
        os.environ["PARL_BACKEND"] = args.backend

    checks = []
    try:
        import parl
        checks.append(item("parl-import", "pass", f"PARL {getattr(parl, '__version__', 'unknown')} imported"))
        for attr in ["Model", "Algorithm", "Agent"]:
            obj = getattr(parl, attr, None)
            if obj is None:
                checks.append(item(f"alias-{attr}", "warn", "not exported; install a DL framework or set PARL_BACKEND before import"))
            else:
                checks.append(item(f"alias-{attr}", "pass", f"{obj.__module__}.{obj.__name__}"))
        if hasattr(parl, "remote_class") and hasattr(parl, "connect"):
            checks.append(item("remote-api", "pass", "remote_class and connect are exported"))
        else:
            checks.append(item("remote-api", "warn", "remote_class/connect missing on this platform or install"))
    except Exception as exc:  # pragma: no cover - diagnostic entry point
        checks.append(item("parl-import", "fail", f"{type(exc).__name__}: {exc}"))

    if args.xparl_help:
        exe = shutil.which("xparl")
        if not exe:
            checks.append(item("xparl-help", "fail", "xparl executable is not on PATH"))
        else:
            for target, cmd in [("root", [exe, "--help"]), ("start", [exe, "start", "--help"]), ("connect", [exe, "connect", "--help"]), ("status", [exe, "status", "--help"]), ("stop", [exe, "stop", "--help"] )]:
                try:
                    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15, check=False)
                    ok = proc.returncode == 0 and "Usage:" in proc.stdout
                    checks.append(item(f"xparl-{target}-help", "pass" if ok else "fail", f"returncode={proc.returncode}"))
                except Exception as exc:
                    checks.append(item(f"xparl-{target}-help", "fail", f"{type(exc).__name__}: {exc}"))

    ok = all(c["status"] in {"pass", "warn"} for c in checks)
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2))
    else:
        for c in checks:
            print(f"[{c['status']}] {c['name']}: {c['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

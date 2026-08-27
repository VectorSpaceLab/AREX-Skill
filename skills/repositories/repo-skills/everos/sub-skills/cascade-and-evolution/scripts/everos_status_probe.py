#!/usr/bin/env python3
"""Safe EverOS status probe for /health and `everos cascade status`."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any


def http_health(base: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(base.rstrip("/") + "/health", timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cascade_status(root: str | None, timeout: float) -> dict[str, Any]:
    exe = shutil.which("everos")
    if not exe:
        return {"ok": False, "error": "everos executable not found on PATH"}
    cmd = [exe, "cascade", "status"]
    if root:
        cmd.extend(["--root", root])
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-url", default="http://127.0.0.1:8000")
    p.add_argument("--root", help="Memory root for cascade status")
    p.add_argument("--health", action="store_true", help="Probe HTTP /health")
    p.add_argument("--cascade-status", action="store_true", help="Run everos cascade status")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if not args.health and not args.cascade_status:
        args.health = True
    out: dict[str, Any] = {}
    rc = 0
    if args.health:
        try:
            out["health"] = {"ok": True, "response": http_health(args.server_url, args.timeout)}
        except Exception as exc:
            out["health"] = {"ok": False, "error": repr(exc)}
            rc = 1
    if args.cascade_status:
        out["cascade_status"] = cascade_status(args.root, args.timeout)
        if not out["cascade_status"].get("ok"):
            rc = 1
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        for name, data in out.items():
            print(f"{name}: {'OK' if data.get('ok') else 'FAIL'}")
            if data.get("stdout"):
                print(data["stdout"])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safely probe TVM RPC API and CLI help without starting services."""
from __future__ import annotations

import argparse
import inspect
import json
import subprocess
import sys


def _help(module: str) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    return {
        "module": module,
        "exit_code": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
        "has_usage": "usage" in (proc.stdout + proc.stderr).lower(),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    import tvm
    from tvm import rpc

    modules = [
        "tvm.exec.rpc_server",
        "tvm.exec.rpc_tracker",
        "tvm.exec.query_rpc_tracker",
        "tvm.exec.rpc_proxy",
    ]
    result = {
        "tvm_version": getattr(tvm, "__version__", None),
        "connect_signature": str(inspect.signature(rpc.connect)),
        "connect_tracker_signature": str(inspect.signature(rpc.connect_tracker)),
        "cli_help": [_help(module) for module in modules],
    }
    ok = all(item["exit_code"] in (0, 1) and item["has_usage"] for item in result["cli_help"])
    result["ok"] = ok
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"tvm_version: {result['tvm_version']}")
        print(f"rpc.connect: {result['connect_signature']}")
        print(f"rpc.connect_tracker: {result['connect_tracker_signature']}")
        for item in result["cli_help"]:
            print(f"{item['module']}: exit={item['exit_code']} usage={item['has_usage']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

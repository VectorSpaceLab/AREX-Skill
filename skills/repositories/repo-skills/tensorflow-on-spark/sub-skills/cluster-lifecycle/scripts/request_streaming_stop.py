#!/usr/bin/env python3
"""Safely request that a TensorFlowOnSpark reservation server stop.

The helper is dry-run by default. It only sends the STOP control message when
`--execute` is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from typing import List, Optional, Tuple


def _single_int_port(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if "-" in value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _resolve_target(host: Optional[str], port: Optional[int]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    if host and port is not None:
        return host, port, None
    if not host and port is None:
        return None, None, "missing reservation server host and port"
    if not host:
        return None, None, "missing reservation server host"
    return None, None, "missing reservation server port"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Request that a TensorFlowOnSpark reservation server stop.",
    )
    parser.add_argument("--host", default=os.environ.get("TFOS_SERVER_HOST"), help="Reservation server host. Defaults to TFOS_SERVER_HOST when set.")
    parser.add_argument("--port", type=int, default=_single_int_port(os.environ.get("TFOS_SERVER_PORT")), help="Reservation server port. Defaults to a single-port TFOS_SERVER_PORT value when available.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Socket timeout in seconds for the stop request.")
    parser.add_argument("--execute", action="store_true", help="Send the STOP control message instead of doing a dry run.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    host, port, error = _resolve_target(args.host, args.port)
    result = {
        "host": host,
        "port": port,
        "execute": bool(args.execute),
        "status": "dry-run" if not args.execute else "pending",
        "error": error,
    }

    if error:
        message = f"{error}; provide --host and --port or set TFOS_SERVER_HOST/TFOS_SERVER_PORT"
        if args.json:
            result["status"] = "error"
            result["error"] = message
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(message, file=sys.stderr)
        return 2

    if not args.execute:
        result["message"] = f"dry run: would request stop from {host}:{port}; re-run with --execute to send the control message"
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["message"])
        return 0

    import_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(args.timeout)
    try:
        from tensorflowonspark import reservation

        client = reservation.Client((host, port))
        response = client.request_stop()
        client.close()
        result["status"] = "ok"
        result["response"] = response
        result["message"] = f"sent STOP to {host}:{port}"
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["message"])
        return 0
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"failed to request stop from {host}:{port}: {exc}", file=sys.stderr)
        return 1
    finally:
        socket.setdefaulttimeout(import_timeout)


if __name__ == "__main__":
    raise SystemExit(main())

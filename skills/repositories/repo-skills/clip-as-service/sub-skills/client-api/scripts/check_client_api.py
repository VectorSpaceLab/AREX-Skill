#!/usr/bin/env python3
"""Safe clip_client.Client API inspection and optional connectivity probe.

Default behavior imports clip_client and prints signatures without contacting a
server. Supplying --server enables an explicit profile/encode probe.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys

os.environ.setdefault("NO_VERSION_CHECK", "1")


def inspect_client() -> dict:
    from clip_client import Client
    import clip_client

    methods = ["profile", "encode", "aencode", "rank", "arank", "index", "aindex", "search", "asearch"]
    return {
        "clip_client_version": getattr(clip_client, "__version__", None),
        "constructor": str(inspect.signature(Client.__init__)),
        "methods": {name: str(inspect.signature(getattr(Client, name))) for name in methods},
    }


def maybe_probe_server(server: str, do_profile: bool, encode_text: str | None, credential: str | None) -> dict:
    from clip_client import Client

    kwargs = {"credential": {"Authorization": credential}} if credential else {}
    client = Client(server, **kwargs)
    result: dict = {"server": server}
    if do_profile:
        result["profile"] = client.profile()
    if encode_text is not None:
        embeddings = client.encode([encode_text])
        result["encode_shape"] = list(getattr(embeddings, "shape", []))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect clip_client.Client and optionally probe a server.")
    parser.add_argument("--server", help="Optional server URI such as grpc://127.0.0.1:51000. Not contacted unless supplied.")
    parser.add_argument("--profile", action="store_true", help="Run Client.profile() against --server.")
    parser.add_argument("--encode-text", help="Encode this single text against --server, wrapped as a one-item list.")
    parser.add_argument("--authorization", help="Optional Authorization token for gRPC/HTTP endpoints.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    report = {"inspection": None, "server_probe": None, "errors": []}
    try:
        report["inspection"] = inspect_client()
    except Exception as exc:  # noqa: BLE001
        report["errors"].append({"phase": "inspect", "error": f"{type(exc).__name__}: {exc}"})

    if args.server:
        try:
            report["server_probe"] = maybe_probe_server(args.server, args.profile, args.encode_text, args.authorization)
        except Exception as exc:  # noqa: BLE001
            report["errors"].append({"phase": "server_probe", "error": f"{type(exc).__name__}: {exc}"})
    elif args.profile or args.encode_text:
        report["errors"].append({"phase": "arguments", "error": "--profile and --encode-text require --server"})

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if report["errors"]:
        print("\nOne or more checks failed. See client troubleshooting for scheme, connectivity, auth, or input-shape recovery.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

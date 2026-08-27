#!/usr/bin/env python3
"""Inspect public Xinference client/API signatures without starting a service.

This helper prints stable facts that future agents can compare with the skill's
references when debugging version drift. It does not contact a Xinference server
or download models.
"""

from __future__ import annotations

import argparse
import inspect
import json
import warnings
from importlib import metadata
from typing import Any


def collect() -> dict[str, Any]:
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch.cuda")
    import xinference  # type: ignore
    from xinference.api.restful_api import RESTfulAPI, _validate_replica  # type: ignore
    from xinference.client import (  # type: ignore
        AsyncClient,
        AsyncRESTfulClient,
        Client,
        RESTfulClient,
    )
    from xinference.client.restful.async_restful_client import (  # type: ignore
        AsyncRESTfulModelHandle,
    )
    from xinference.client.restful.restful_client import (  # type: ignore
        RESTfulEmbeddingModelHandle,
        RESTfulModelHandle,
        RESTfulRerankModelHandle,
    )

    try:
        dist_version = metadata.version("xinference")
    except metadata.PackageNotFoundError:
        dist_version = getattr(xinference, "__version__", "unknown")

    signatures = {
        "Client": inspect.signature(Client),
        "Client.launch_model": inspect.signature(Client.launch_model),
        "Client.register_model": inspect.signature(Client.register_model),
        "Client.get_model": inspect.signature(Client.get_model),
        "Client.list_models": inspect.signature(Client.list_models),
        "Client.list_model_registrations": inspect.signature(Client.list_model_registrations),
        "Client.terminate_model": inspect.signature(Client.terminate_model),
        "AsyncClient": inspect.signature(AsyncClient),
        "AsyncClient.launch_model": inspect.signature(AsyncClient.launch_model),
        "RESTfulModelHandle.close": inspect.signature(RESTfulModelHandle.close),
        "RESTfulEmbeddingModelHandle.create_embedding": inspect.signature(
            RESTfulEmbeddingModelHandle.create_embedding
        ),
        "RESTfulRerankModelHandle.rerank": inspect.signature(
            RESTfulRerankModelHandle.rerank
        ),
        "AsyncRESTfulModelHandle.close": inspect.signature(AsyncRESTfulModelHandle.close),
        "RESTfulAPI.__init__": inspect.signature(RESTfulAPI.__init__),
        "_validate_replica": inspect.signature(_validate_replica),
    }

    entry_points = sorted(
        ep.name for ep in metadata.entry_points(group="console_scripts") if ep.name.startswith("xinference")
    )

    return {
        "version": dist_version,
        "aliases": {
            "RESTfulClient_is_Client": RESTfulClient is Client,
            "AsyncRESTfulClient_is_AsyncClient": AsyncRESTfulClient is AsyncClient,
        },
        "signatures": {key: str(value) for key, value in signatures.items()},
        "console_entry_points": entry_points,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print selected Xinference public signatures and entry points."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        data = collect()
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"ERROR: could not inspect Xinference interfaces: {type(exc).__name__}: {exc}")
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Xinference version: {data['version']}")
        print("Aliases:")
        for name, ok in data["aliases"].items():
            print(f"  {name}: {ok}")
        print("Console entry points:")
        for name in data["console_entry_points"]:
            print(f"  {name}")
        print("Signatures:")
        for name, sig in data["signatures"].items():
            print(f"  {name}{sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a Gateway OpenAPI schema from a Flow/Gateway config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="gateway.json", help="Output OpenAPI JSON path.")
    parser.add_argument("--protocol", default="grpc", help="Gateway protocol to model.")
    parser.add_argument("--port", type=int, default=12345, help="Local port recorded in the schema.")
    args = parser.parse_args()

    try:
        from jina.parsers import set_gateway_parser
        from jina.serve.runtimes.gateway.http_fastapi_app import get_fastapi_app
        from jina.serve.runtimes.gateway.streamer import GatewayStreamer
        from jina.logging.logger import JinaLogger

        namespace = set_gateway_parser().parse_args([])
        namespace.port = args.port
        namespace.protocol = [args.protocol]
        logger = JinaLogger("gateway-openapi")
        streamer = GatewayStreamer(
            graph_representation={},
            executor_addresses={},
            graph_conditions={},
            deployments_no_reduce=[],
            timeout_send=namespace.timeout_send,
            retries=namespace.retries,
            compression=namespace.compression,
            runtime_name=namespace.name,
            prefetch=namespace.prefetch,
            logger=logger,
        )
        app = get_fastapi_app(
            streamer=streamer,
            title=namespace.title,
            description=namespace.description,
            no_debug_endpoints=namespace.no_debug_endpoints,
            no_crud_endpoints=namespace.no_crud_endpoints,
            expose_endpoints=namespace.expose_endpoints,
            expose_graphql_endpoint=namespace.expose_graphql_endpoint,
            cors=namespace.cors,
            logger=logger,
        )
        schema = app.openapi()
    except Exception as exc:  # pragma: no cover - depends on installed FastAPI/Pydantic/Jina mix
        print(
            "Gateway OpenAPI export failed. This helper uses Jina Gateway/FastAPI internals and is sensitive "
            "to FastAPI/Pydantic/DocArray compatibility. Align those package versions, or use "
            "`jina export schema --json-path <file>` for Jina's general API schema. "
            f"Original error: {exc!r}",
            file=sys.stderr,
        )
        return 2
    Path(args.output).write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

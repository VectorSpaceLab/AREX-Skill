#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: python-import-smoke.sh [--help]

Import the Strands Python SDK and Strands MCP server package with python from
PATH, print key distribution versions and signatures, and avoid network,
credentials, provider calls, and native tests.

Run this in an environment where the packages are installed. It is safe to run
outside a checkout.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

python - <<'PY'
from importlib.metadata import PackageNotFoundError, version
import importlib
import inspect

for dist in ["strands-agents", "strands-agents-mcp-server"]:
    try:
        print(f"{dist}={version(dist)}")
    except PackageNotFoundError:
        raise SystemExit(f"missing distribution: {dist}")

from strands import Agent, tool
print("Agent.__init__", inspect.signature(Agent.__init__))
print("Agent.__call__", inspect.signature(Agent.__call__))
print("tool", inspect.signature(tool))

server = importlib.import_module("strands_mcp_server.server")
print("mcp app", getattr(server, "APP_NAME", None))
print("search_docs", inspect.signature(server.search_docs))
print("fetch_doc", inspect.signature(server.fetch_doc))
print("python import smoke passed")
PY

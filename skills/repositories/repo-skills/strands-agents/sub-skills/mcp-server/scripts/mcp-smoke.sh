#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: mcp-smoke.sh [--help]

Import the strands-agents MCP server package with python from PATH and print the
verified public tool signatures. If the console entry point is installed, also
check that `strands-agents-mcp-server --help` exits successfully.

This smoke check does not call cache.ensure_ready(), search_docs(), or fetch_doc(),
so it does not fetch network documentation by default.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "Unknown argument: $1" >&2
  usage >&2
  exit 2
fi

python - <<'PY'
from inspect import signature

try:
    from strands_mcp_server.server import APP_NAME, fetch_doc, search_docs
except Exception as exc:  # pragma: no cover - shell smoke diagnostics
    raise SystemExit(f"MCP server import failed: {exc}") from exc

if APP_NAME != "strands-agents-mcp-server":
    raise SystemExit(f"unexpected APP_NAME: {APP_NAME!r}")

search_sig = signature(search_docs)
fetch_sig = signature(fetch_doc)

if list(search_sig.parameters) != ["query", "k"] or search_sig.parameters["k"].default != 5:
    raise SystemExit(f"unexpected search_docs signature: {search_sig}")

if (
    list(fetch_sig.parameters) != ["uri", "section"]
    or fetch_sig.parameters["uri"].default != ""
    or fetch_sig.parameters["section"].default != ""
):
    raise SystemExit(f"unexpected fetch_doc signature: {fetch_sig}")

print(f"APP_NAME={APP_NAME}")
print(f"search_docs{search_sig}")
print(f"fetch_doc{fetch_sig}")
PY

if command -v strands-agents-mcp-server >/dev/null 2>&1; then
  strands-agents-mcp-server --help >/dev/null
  echo "console entry point: OK"
else
  echo "console entry point: not installed on PATH; skipped"
fi

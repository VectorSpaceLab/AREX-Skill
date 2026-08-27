#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: mcp-smoke.sh [--install] [--skip-tests] [--skip-smoke] [--stdio-only] [--http-only] [--port PORT]

Safe diagnostics for the Airweave MCP search server.

Defaults:
  - resolve the repo root from this script location
  - require existing Node/npm dependencies
  - run build and targeted tests
  - run stdio and HTTP smoke checks against mock-friendly local settings

Options:
  --install      Run npm install inside mcp/ before checks.
  --skip-tests   Skip npm run test:mcp, npm run test:http, and npm run test:oauth.
  --skip-smoke   Skip entrypoint smoke checks.
  --stdio-only   Run only the stdio smoke check.
  --http-only    Run only the HTTP smoke check.
  --port PORT    HTTP smoke port, default: 18080.
  --help         Show this help.
EOF
}

info() {
  printf '→ %s\n' "$*"
}

fail() {
  printf '❌ %s\n' "$*" >&2
  exit 1
}

run() {
  printf '+ %s\n' "$*"
  "$@"
}

resolve_repo_root() {
  local script_dir git_root fallback_root
  script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  if git_root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null); then
    printf '%s\n' "$git_root"
    return 0
  fi
  fallback_root=$(cd "$script_dir/../../../../../.." && pwd)
  printf '%s\n' "$fallback_root"
}

stdio_smoke() {
  local log_file pid started=0 i
  log_file=$(mktemp)
  env \
    AIRWEAVE_API_KEY=test-key \
    AIRWEAVE_COLLECTION=test-collection \
    AIRWEAVE_BASE_URL=http://localhost:8001 \
    node build/index.js >"$log_file" 2>&1 &
  pid=$!

  for i in $(seq 1 40); do
    if grep -q "Airweave MCP Search Server started" "$log_file"; then
      started=1
      break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done

  if [[ "$started" -ne 1 ]]; then
    printf '\n--- stdio smoke log ---\n' >&2
    cat "$log_file" >&2 || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$log_file"
    fail "stdio entrypoint did not print the startup banner"
  fi

  if ! grep -q "Collection: test-collection" "$log_file"; then
    cat "$log_file" >&2 || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$log_file"
    fail "stdio entrypoint did not report the expected collection"
  fi

  if ! grep -q "Base URL: http://localhost:8001" "$log_file"; then
    cat "$log_file" >&2 || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$log_file"
    fail "stdio entrypoint did not report the expected base URL"
  fi

  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -f "$log_file"
  info "stdio smoke passed"
}

http_smoke() {
  local port="$1"
  local log_file pid i ready=0 status=0
  log_file=$(mktemp)
  env \
    AIRWEAVE_API_KEY=test-key \
    AIRWEAVE_COLLECTION=test-collection \
    AIRWEAVE_BASE_URL=http://localhost:8001 \
    PORT="$port" \
    node build/index-http.js >"$log_file" 2>&1 &
  pid=$!

  for i in $(seq 1 60); do
    if node -e "fetch('http://127.0.0.1:${port}/health').then(async (r) => { if (!r.ok) process.exit(1); const j = await r.json(); if (j.transport !== 'streamable-http') process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      ready=1
      break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done

  if [[ "$ready" -ne 1 ]]; then
    printf '\n--- HTTP smoke log ---\n' >&2
    cat "$log_file" >&2 || true
    status=1
  else
    if ! node -e "fetch('http://127.0.0.1:${port}/').then(async (r) => { const j = await r.json(); if (j.endpoints?.mcp !== '/mcp') process.exit(1); if (j.authentication?.required !== true) process.exit(1); if (j.mode !== 'stateless') process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      status=1
    fi

    if ! node -e "fetch('http://127.0.0.1:${port}/metrics').then(async (r) => { const text = await r.text(); if (!text.includes('nodejs_')) process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      status=1
    fi

    if ! node -e "fetch('http://127.0.0.1:${port}/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-key', 'X-Collection-Readable-ID': 'test-collection' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/list', id: 1 }) }).then(async (r) => { if (!r.ok) process.exit(1); const j = await r.json(); const tools = j.result?.tools ?? []; if (!tools.some((t) => t.name === 'search-test-collection')) process.exit(1); if (!tools.some((t) => t.name === 'get-config')) process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      status=1
    fi

    if ! node -e "fetch('http://127.0.0.1:${port}/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-key', 'X-Collection-Readable-ID': 'test-collection' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'search-test-collection', arguments: { query: 'smoke' } }, id: 2 }) }).then(async (r) => { if (!r.ok) process.exit(1); const j = await r.json(); const text = JSON.stringify(j); if (!text.includes('Collection')) process.exit(1); if (!text.includes('smoke')) process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      status=1
    fi

    if ! node -e "fetch('http://127.0.0.1:${port}/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-key', 'X-Collection-Readable-ID': 'test-collection' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'get-config', arguments: {} }, id: 3 }) }).then(async (r) => { if (!r.ok) process.exit(1); const j = await r.json(); const text = JSON.stringify(j); if (!text.includes('test-collection')) process.exit(1); }).then(() => process.exit(0)).catch(() => process.exit(1))" >/dev/null 2>&1; then
      status=1
    fi
  fi

  if [[ "$status" -ne 0 ]]; then
    printf '\n--- HTTP smoke log ---\n' >&2
    cat "$log_file" >&2 || true
  fi

  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -f "$log_file"

  if [[ "$status" -ne 0 ]]; then
    fail "HTTP smoke checks failed"
  fi

  info "HTTP smoke passed"
}

main() {
  local install=0 skip_tests=0 skip_smoke=0 stdio_only=0 http_only=0 http_port=18080

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --install)
        install=1
        ;;
      --skip-tests)
        skip_tests=1
        ;;
      --skip-smoke)
        skip_smoke=1
        ;;
      --stdio-only)
        stdio_only=1
        ;;
      --http-only)
        http_only=1
        ;;
      --port)
        [[ $# -ge 2 ]] || fail "--port requires a value"
        http_port="$2"
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        fail "Unknown argument: $1"
        ;;
    esac
    shift
  done

  if [[ "$stdio_only" -eq 1 && "$http_only" -eq 1 ]]; then
    fail "--stdio-only and --http-only cannot be combined"
  fi

  local repo_root mcp_dir package_name package_version
  repo_root=$(resolve_repo_root)
  mcp_dir="$repo_root/mcp"
  [[ -d "$mcp_dir" ]] || fail "Could not find mcp/ under $repo_root"

  cd "$mcp_dir"

  command -v node >/dev/null 2>&1 || fail "Node.js is not installed"
  command -v npm >/dev/null 2>&1 || fail "npm is not installed"

  info "Node: $(node -v)"
  info "npm: $(npm -v)"

  package_name=$(node -p "require('./package.json').name")
  package_version=$(node -p "require('./package.json').version")
  info "Package: ${package_name} ${package_version}"

  if [[ "$install" -eq 1 ]]; then
    run npm install
  elif [[ ! -d node_modules ]]; then
    fail "Dependencies are missing. Re-run with --install to install them, or run npm install inside $mcp_dir."
  fi

  run npm run build

  if [[ "$skip_tests" -eq 0 ]]; then
    run npm run test:mcp
    run npm run test:http
    run npm run test:oauth
  fi

  if [[ "$skip_smoke" -eq 0 ]]; then
    if [[ "$http_only" -eq 0 ]]; then
      stdio_smoke
    fi
    if [[ "$stdio_only" -eq 0 ]]; then
      http_smoke "$http_port"
    fi
  fi

  info "All requested MCP smoke checks passed"
}

main "$@"

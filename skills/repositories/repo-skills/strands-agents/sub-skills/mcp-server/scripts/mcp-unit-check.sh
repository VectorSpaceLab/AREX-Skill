#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: mcp-unit-check.sh [--help] [--root CHECKOUT_OR_PACKAGE_ROOT]

Run selected offline pytest tests for the Strands Agents MCP server package.
Invoke from a checkout that contains the MCP server package, or from the package
root itself, with an active Python environment that has the package plus test
dependencies installed.

Options:
  --root CHECKOUT_OR_PACKAGE_ROOT  Checkout root or MCP package root.
  --help, -h                       Show this help text.

This helper intentionally does not run live integration tests.
EOF
}

find_checkout_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/strands-mcp/pyproject.toml" && -d "$dir/strands-mcp/tests" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    if [[ -f "$dir/pyproject.toml" && -d "$dir/tests" ]] && grep -q 'name = "strands-agents-mcp-server"' "$dir/pyproject.toml"; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

package_dir_for_root() {
  local candidate="$1"
  if [[ -f "$candidate/strands-mcp/pyproject.toml" && -d "$candidate/strands-mcp/tests" ]]; then
    printf '%s\n' "$candidate/strands-mcp"
    return 0
  fi
  if [[ -f "$candidate/pyproject.toml" && -d "$candidate/tests" ]] && grep -q 'name = "strands-agents-mcp-server"' "$candidate/pyproject.toml"; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

root=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --root)
      if [[ $# -lt 2 ]]; then
        echo "--root requires a path" >&2
        exit 2
      fi
      root="$2"
      shift 2
      ;;
    --root=*)
      root="${1#--root=}"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$root" ]]; then
  if ! root="$(find_checkout_root "$PWD")"; then
    echo "Could not find a checkout or package root containing the MCP server pyproject." >&2
    echo "Run from that checkout/package root or pass --root CHECKOUT_OR_PACKAGE_ROOT." >&2
    exit 2
  fi
fi

if ! pkg_dir="$(package_dir_for_root "$root")"; then
  echo "Not a compatible checkout or package root: $root" >&2
  exit 2
fi

python - <<'PY'
import importlib

missing = []
for name in ("pytest", "strands_mcp_server"):
    try:
        importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - shell helper diagnostics
        missing.append(f"{name}: {exc}")

if missing:
    raise SystemExit("Missing test dependency/imports:\n" + "\n".join(missing))
PY

cd "$pkg_dir"
python -m pytest -q \
  tests/test_dependencies.py \
  tests/test_server.py \
  tests/test_indexer.py \
  tests/test_cache.py \
  tests/test_indexer_concurrency.py \
  tests/test_text_processor.py

#!/usr/bin/env bash
# Verify the CLI toolchain for Instill Core workflows.
#
# Safe by default: this script only checks tool presence and, when a repo root
# is supplied, performs read-only readiness checks such as `docker compose
# config` or `make help`.
#
# Examples:
#   scripts/check-toolchain.sh --mode compose --repo-root /path/to/instill-core
#   scripts/check-toolchain.sh --mode integration

set -euo pipefail

mode="all"
repo_root=""

usage() {
  cat <<'EOF'
Usage: check-toolchain.sh [--mode compose|helm|integration|release|all] [--repo-root PATH]

Modes:
  compose       Docker Compose and local-stack tooling
  helm          Helm/Kubernetes tooling
  integration   Compose/model integration tooling
  release       Local release-maintenance tooling
  all           Check every mode
EOF
}

warn() { printf 'WARN: %s\n' "$*" >&2; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '  [ok] %s -> %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf '  [missing] %s\n' "$cmd"
    return 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --repo-root)
      repo_root="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$mode" ]] || fail "--mode requires a value"

check_compose() {
  printf '\nCompose toolchain\n'
  local missing=0
  need docker || missing=1
  need make || missing=1
  need jq || missing=1
  if command -v nvidia-smi >/dev/null 2>&1; then
    printf '  [gpu] nvidia-smi detected; the Makefile will pick the NVIDIA compose path\n'
    need yq || missing=1
  else
    printf '  [cpu] no nvidia-smi detected; CPU compose path is expected\n'
  fi
  if [[ -n "$repo_root" && -f "$repo_root/docker-compose.yml" ]]; then
    if command -v docker >/dev/null 2>&1; then
      if docker compose --project-directory "$repo_root" -f "$repo_root/docker-compose.yml" config >/dev/null 2>&1; then
        printf '  [ok] docker compose config for base stack\n'
      else
        warn "docker compose config for base stack could not be rendered yet"
      fi
    fi
  fi
  return "$missing"
}

check_helm() {
  printf '\nHelm toolchain\n'
  local missing=0
  need helm || missing=1
  need kubectl || missing=1
  need make || missing=1
  if [[ -n "$repo_root" && -f "$repo_root/charts/core/Chart.yaml" ]]; then
    if command -v helm >/dev/null 2>&1; then
      if helm dependency list "$repo_root/charts/core" >/dev/null 2>&1; then
        printf '  [ok] chart dependency metadata is readable\n'
      else
        warn "chart dependency metadata is not fully resolved yet; run helm dependency update when you need install/render"
      fi
    fi
  fi
  return "$missing"
}

check_integration() {
  printf '\nIntegration toolchain\n'
  local missing=0
  need docker || missing=1
  need make || missing=1
  need jq || missing=1
  need python3 || missing=1
  need instill || missing=1
  if [[ -n "$repo_root" && -f "$repo_root/integration-test/models/inventory.json" ]]; then
    printf '  [ok] model inventory file exists\n'
  fi
  return "$missing"
}

check_release() {
  printf '\nRelease toolchain\n'
  local missing=0
  need git || missing=1
  need python3 || missing=1
  if [[ -n "$repo_root" && -f "$repo_root/release-please/config.json" ]]; then
    printf '  [ok] release-please config exists\n'
  fi
  return "$missing"
}

status=0
case "$mode" in
  compose)
    check_compose || status=1
    ;;
  helm)
    check_helm || status=1
    ;;
  integration)
    check_integration || status=1
    ;;
  release)
    check_release || status=1
    ;;
  all)
    check_compose || status=1
    check_helm || status=1
    check_integration || status=1
    check_release || status=1
    ;;
  *)
    fail "unknown mode: $mode"
    ;;
esac

if [[ $status -eq 0 ]]; then
  printf '\nToolchain looks ready for %s workflows.\n' "$mode"
else
  printf '\nToolchain is missing prerequisites for %s workflows.\n' "$mode"
fi
exit "$status"

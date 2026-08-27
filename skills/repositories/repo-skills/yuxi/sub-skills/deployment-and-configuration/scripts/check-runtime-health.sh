#!/usr/bin/env bash
# Read-only Yuxi runtime health probe. It checks Compose service state and
# public health endpoints without starting, stopping, rebuilding, seeding, or
# editing environment files.

set -uo pipefail

mode="dev"
project_dir="."
compose_file=""
base_url=""
api_health_url=""
tail_lines=40
show_logs=0
skip_curl=0
failures=0
checks=0

usage() {
  cat <<'USAGE'
Usage: check-runtime-health.sh [--dev|--prod] [options]

Options:
  --dev                    Use docker-compose.yml and local dev URLs (default).
  --prod                   Use docker-compose.prod.yml and production URLs.
  --project-dir DIR        Directory containing the Compose file (default: .).
  --compose-file FILE      Compose file name/path, relative to project dir unless absolute.
  --base-url URL           Public root URL; health is checked at URL/api/system/health.
  --api-health-url URL     Exact API health URL to check.
  --tail N                 Log lines per service when --logs is set (default: 40).
  --logs                   Also print bounded logs for key services (may reveal local data).
  --no-curl                Skip HTTP endpoint checks.
  -h, --help               Show this help.

This script is read-only. It never runs docker compose up/down/restart/build,
never edits .env files, and never prints environment variable values.
USAGE
}

note() { printf '\n== %s ==\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1" >&2; }
fail() { printf 'FAIL: %s\n' "$1" >&2; failures=$((failures + 1)); }
pass() { printf 'PASS: %s\n' "$1"; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dev) mode="dev" ;;
    --prod) mode="prod" ;;
    --project-dir)
      shift || { fail "--project-dir needs a value"; exit 2; }
      project_dir="$1"
      ;;
    --compose-file)
      shift || { fail "--compose-file needs a value"; exit 2; }
      compose_file="$1"
      ;;
    --base-url)
      shift || { fail "--base-url needs a value"; exit 2; }
      base_url="$1"
      ;;
    --api-health-url)
      shift || { fail "--api-health-url needs a value"; exit 2; }
      api_health_url="$1"
      ;;
    --tail)
      shift || { fail "--tail needs a value"; exit 2; }
      tail_lines="$1"
      ;;
    --logs) show_logs=1 ;;
    --no-curl) skip_curl=1 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown option: $1"; usage; exit 2 ;;
  esac
  shift
done

case "$tail_lines" in
  ''|*[!0-9]*) fail "--tail must be a non-negative integer"; exit 2 ;;
esac

if [ -z "$compose_file" ]; then
  if [ "$mode" = "prod" ]; then
    compose_file="docker-compose.prod.yml"
  else
    compose_file="docker-compose.yml"
  fi
fi

if [ -z "$api_health_url" ]; then
  if [ -n "$base_url" ]; then
    root="${base_url%/}"
    api_health_url="$root/api/system/health"
  elif [ "$mode" = "prod" ]; then
    api_health_url="http://localhost/api/system/health"
  else
    api_health_url="http://localhost:5050/api/system/health"
  fi
fi

if [ "$mode" = "prod" ]; then
  web_url="${base_url:-http://localhost}"
else
  web_url="${base_url:-http://localhost:5173}"
fi
web_url="${web_url%/}/"

compose_path="$compose_file"
case "$compose_path" in
  /*) ;;
  *) compose_path="$project_dir/$compose_path" ;;
esac

compose() {
  docker compose --project-directory "$project_dir" -f "$compose_path" "$@"
}

note "Yuxi runtime probe"
printf 'Mode: %s\n' "$mode"
printf 'Project dir: %s\n' "$project_dir"
printf 'Compose file: %s\n' "$compose_file"
printf 'API health URL: %s\n' "$api_health_url"

if command -v docker >/dev/null 2>&1 && [ -f "$compose_path" ]; then
  note "Compose services"
  services="$(compose config --services 2>/dev/null || true)"
  if [ -z "$services" ]; then
    fail "could not read Compose services; check file, project dir, and required env variable names"
  else
    checks=$((checks + 1))
    printf '%s\n' "$services" | sed 's/^/- /'
    pass "Compose service list is readable"
  fi

  note "docker compose ps"
  if compose ps; then
    checks=$((checks + 1))
  else
    fail "docker compose ps failed"
  fi

  note "Container health summary"
  for svc in api worker web sandbox-provisioner postgres redis minio milvus graph etcd mineru-api paddlex; do
    if ! printf '%s\n' "$services" | grep -qx "$svc"; then
      continue
    fi
    cid="$(compose ps -q "$svc" 2>/dev/null | head -n 1 || true)"
    if [ -z "$cid" ]; then
      printf '%-22s %s\n' "$svc" "not created or not running"
      continue
    fi
    checks=$((checks + 1))
    state="$(docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cid" 2>/dev/null || true)"
    if [ -z "$state" ]; then
      fail "$svc: docker inspect failed"
      continue
    fi
    printf '%-22s %s\n' "$svc" "$state"
    case "$state" in
      *unhealthy*|exited*|dead*) fail "$svc is not healthy/running" ;;
    esac
  done

  if [ "$show_logs" -eq 1 ]; then
    note "Bounded logs"
    warn "Container logs can include local paths or sensitive operational data. Redact before sharing."
    compose logs --tail="$tail_lines" api worker web sandbox-provisioner 2>&1 || warn "some service logs were unavailable"
  fi
else
  if ! command -v docker >/dev/null 2>&1; then
    warn "docker command not found; skipping Compose checks"
  else
    warn "Compose file not found at $compose_path; skipping Compose checks"
  fi
fi

if [ "$skip_curl" -eq 0 ]; then
  if command -v curl >/dev/null 2>&1; then
    note "HTTP health endpoints"
    tmp="${TMPDIR:-/tmp}/yuxi-health.$$"
    if curl -fsS --max-time 8 "$api_health_url" > "$tmp"; then
      checks=$((checks + 1))
      pass "API health endpoint responded"
      sed 's/^/  /' "$tmp"
    else
      fail "API health endpoint failed: $api_health_url"
    fi
    rm -f "$tmp"

    if curl -fsS --max-time 8 -o /dev/null "$web_url"; then
      checks=$((checks + 1))
      pass "Web endpoint responded: $web_url"
    else
      fail "Web endpoint failed: $web_url"
    fi

    if [ "$mode" = "dev" ]; then
      sandbox_url="http://localhost:8002/health"
      if curl -fsS --max-time 5 -o /dev/null "$sandbox_url"; then
        checks=$((checks + 1))
        pass "Sandbox provisioner health endpoint responded"
      else
        warn "Sandbox provisioner dev loopback endpoint did not respond; it may be stopped, not exposed, or prod-like"
      fi
    fi
  else
    warn "curl not found; skipping HTTP checks"
  fi
fi

note "Result"
if [ "$checks" -eq 0 ]; then
  fail "no checks could be executed"
fi

if [ "$failures" -eq 0 ]; then
  pass "No failed read-only checks"
  exit 0
fi

fail "$failures read-only check(s) failed"
exit 1

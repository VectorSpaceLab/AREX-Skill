#!/usr/bin/env bash
# Diagnose Docker/Compose readiness for an OWL deployment without side effects.
# This helper never builds images, starts/stops services, prints secret values,
# or assumes a repository checkout-relative working directory.
set -u

usage() {
  cat <<'EOF'
Usage: check_docker_runtime.sh [--env-file PATH]

Checks Docker executable/daemon and Docker Compose availability. When an env
file is supplied, reports only whether non-comment values appear blank or look
like placeholders; secret values are never printed. No container is changed.
EOF
}

env_file=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) env_file=${2:-}; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

status=0
if ! command -v docker >/dev/null 2>&1; then
  echo "docker: missing"
  status=1
else
  echo "docker: $(command -v docker)"
  if docker info >/dev/null 2>&1; then
    echo "docker daemon: reachable"
  else
    echo "docker daemon: unavailable or permission denied"
    status=1
  fi
fi

if command -v docker-compose >/dev/null 2>&1; then
  echo "compose: docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "compose: docker compose"
else
  echo "compose: missing"
  status=1
fi

if [[ -n "$env_file" ]]; then
  if [[ ! -f "$env_file" ]]; then
    echo "env file: missing"
    status=1
  else
    total=0
    placeholders=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line=${line#"${line%%[![:space:]]*}"}
      [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
      total=$((total + 1))
      value=${line#*=}
      value=${value#\"}; value=${value%\"}; value=${value#\'}; value=${value%\'}
      lower=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')
      if [[ -z "$lower" || "$lower" == *your_key* || "$lower" == *your-api-key* || "$lower" == *your_id* ]]; then
        placeholders=$((placeholders + 1))
      fi
    done < "$env_file"
    echo "env file: $total configured names; $placeholders blank/placeholder values"
  fi
fi

exit "$status"

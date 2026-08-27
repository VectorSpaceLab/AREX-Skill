#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_openapi_schema.sh [--check|--generate] [--repo PATH]

Run Kiln's OpenAPI schema bridge from a Kiln checkout.

Options:
  --check       Verify app/web_ui/src/lib/api_schema.d.ts is current. This is the default.
  --generate    Regenerate app/web_ui/src/lib/api_schema.d.ts in the checkout.
  --repo PATH   Kiln checkout root. Defaults to the current working directory.
  -h, --help    Show this help.

Notes:
  - This wrapper must run against a Kiln checkout containing app/web_ui/src/lib/.
  - --check is read-only except for temporary files created by the repo script.
  - --generate intentionally updates the checkout's generated TypeScript schema.
  - If KILN_PORT is set and responds, the repo script fetches /openapi.json;
    otherwise it imports app.desktop.desktop_server.make_app().openapi().
EOF
}

mode="check"
repo="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      mode="check"
      shift
      ;;
    --generate)
      mode="generate"
      shift
      ;;
    --repo)
      if [[ $# -lt 2 ]]; then
        echo "error: --repo requires a path" >&2
        exit 2
      fi
      repo="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

repo="$(cd "$repo" && pwd)"
lib_dir="$repo/app/web_ui/src/lib"

if [[ ! -d "$lib_dir" ]]; then
  echo "error: $repo does not look like a Kiln checkout; missing app/web_ui/src/lib" >&2
  exit 2
fi

export KILN_SKIP_REMOTE_MODEL_LIST="${KILN_SKIP_REMOTE_MODEL_LIST:-true}"

case "$mode" in
  check)
    script="$lib_dir/check_schema.sh"
    ;;
  generate)
    script="$lib_dir/generate_schema.sh"
    ;;
  *)
    echo "error: invalid mode: $mode" >&2
    exit 2
    ;;
esac

cd "$repo"
bash "$script"

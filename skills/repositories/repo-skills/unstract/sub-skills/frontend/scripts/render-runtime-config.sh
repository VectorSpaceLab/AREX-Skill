#!/usr/bin/env bash
# Render the Unstract frontend runtime config to a user-chosen file.
#
# This is a bundled, self-contained adaptation of the repo's runtime-config
# generator. It avoids the hard-coded Nginx path and can be used for local
# inspection, tests, or container entrypoints that want a different target.

set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: render-runtime-config.sh [--output PATH]

Options:
  --output PATH   Output file to write (default: ./runtime-config.js)
  -h, --help      Show this help and exit
EOF
}

output="runtime-config.js"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

js_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

mkdir -p "$(dirname "$output")"

app_version=$(js_escape "${UNSTRACT_APPS_VERSION:-}")

cat > "$output" <<EOF
// This file is auto-generated at runtime. Do not modify manually.
window.RUNTIME_CONFIG = {
  faviconPath: "${VITE_FAVICON_PATH:-${REACT_APP_FAVICON_PATH:-/favicon.ico}}",
  logoUrl: "${VITE_CUSTOM_LOGO_URL:-${REACT_APP_CUSTOM_LOGO_URL:-}}",
  enablePosthog: "${VITE_ENABLE_POSTHOG:-${REACT_APP_ENABLE_POSTHOG:-}}",
  version: "${app_version}"
};
EOF

chmod 644 "$output"

echo "Wrote runtime config to $output"
